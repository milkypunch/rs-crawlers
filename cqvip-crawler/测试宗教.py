import redis
import pymongo
import requests
import execjs
from lxml import etree
from requests.exceptions import RequestException
import json
import hashlib
from retrying import retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class CnJournal:
    def __init__(self):
        self.mongo_client = pymongo.MongoClient()
        self.collection = self.mongo_client['py_spider']['cn_journal_psy']
        
        self.url = 'https://qikan.cqvip.com/Qikan/Journal/JournalGuid?from=index'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        self.cookies = {}
        self.session = requests.Session()
        self.redis_client = redis.Redis()

     
    def get_cookie(self):
        res = self.session.get(self.url, headers=self.headers)
        tree = etree.HTML(res.text) 
        
        content = tree.xpath("//meta[2]/@content")[0] 
        ts_code_str = tree.xpath("//script[1]/text()")[0]
        js_file_src = tree.xpath("//script[2]/@src")[0]
        js_file_url = "https://qikan.cqvip.com" + js_file_src
        response = requests.get(js_file_url, headers=self.headers)

        iife_code = response.text
        with open("外链测试.js", 'w') as f:
            f.write(iife_code)

        with open("替换变量.js", encoding='utf-8') as f:
            js_code = f.read().replace("content_value", content).replace('"ts_code_str"', ts_code_str)

        cookie = execjs.compile(js_code).call("getCookie")
        cookie = cookie.split(";")[0]
        self.cookies = {
            cookie.split('=')[0]: cookie.split('=')[1]
        }

    @staticmethod
    def format_data(page):
        data = {
            "searchParamModel": "{\"ObjectType\":7,\"SearchKeyList\":[],\"SearchExpression\":null,\"BeginYear\":null,\"EndYear\":null,\"UpdateTimeType\":null,\"JournalRange\":null,\"DomainRange\":null,\"ClusterFilter\":\"ZY=8#哲学宗教\",\"ClusterLimit\":0,\"ClusterUseType\":\"Article\",\"UrlParam\":\"\",\"Sort\":\"1\",\"SortField\":null,\"UserID\":\"0\",\"PageNum\":1,\"PageSize\":20,\"SType\":null,\"StrIds\":null,\"IsRefOrBy\":0,\"ShowRules\":\"\",\"IsNoteHistory\":0,\"AdvShowTitle\":null,\"ObjectId\":null,\"ObjectSearchType\":0,\"ChineseEnglishExtend\":0,\"SynonymExtend\":0,\"ShowTotalCount\":0,\"AdvTabGuid\":\"\"}"
        }
        search_param_model = json.loads(data["searchParamModel"])
        search_param_model["PageNum"] = page
        data["searchParamModel"] = json.dumps(search_param_model, ensure_ascii=False)
        return data
    
    @retry(stop_max_attempt_number=5)
    def fetch_level_one_data(self, page_num):
        url = "https://qikan.cqvip.com/Search/SearchList"
        data = self.format_data(page_num)
        response = self.session.post(url, headers=self.headers, cookies=self.cookies, data=data)
        
        if response.status_code == 200:
            return response

        else:
            time.sleep(2)
            self.get_cookie()
            print("cookie refreshed: ", self.cookies)
            raise RequestException(f"一级页面请求失败，状态码：{response.status_code}")
             
    def parse_level_one(self, response):
        tree = etree.HTML(response.text)
        rows = tree.xpath('//tbody/tr')
        journal_links = []
        for row in rows:
            a_tag = row.xpath('.//td[@class="title"]/a')
            journal_name = a_tag[0].text if a_tag else None
            href_value = a_tag[0].get('href') if a_tag else None
            summary_url = f"https://qikan.cqvip.com{href_value}"
            journal_links.append((journal_name, summary_url))

        return journal_links
    
    @retry(stop_max_attempt_number=5)
    def fetch_level_two(self, url):
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)
        if response.status_code == 200:
            return response
        else:
            time.sleep(2)
            self.get_cookie()
            print("cookie refreshed: ", self.cookies)
            raise RequestException(f"二级页面请求失败，状态码：{response.status_code}")
             
    def fetch_detail(self, summary_url):
        response = self.fetch_level_two(summary_url)
        if response: 
            tree = etree.HTML(response.text) 
            # 'NoneType' object has no attribute 'text' 
            detail_href = tree.xpath('//div[@class="object-tab"]/ul/li[1]/a/@href')[0]
            detail_url = f"https://qikan.cqvip.com{detail_href}"
            response = self.fetch_level_two(detail_url)
            return response
        else:
            print("response: ", type(response))

    @staticmethod
    def parse_detail_page(response):
        tree = etree.HTML(response.text)

        # 提取期刊信息
        journal_info = {}
        for li in tree.xpath('//div[@class="info-left"]//ul/li'):
            label = li.xpath('.//span[@class="label"]/text()')
            if label:
                label_text = label[0].strip()
                # 获取值，特别处理电子邮件
                if '电子邮件' in label_text:
                    email = li.xpath('.//a/span/text()')
                    value = email[0].strip() if email else None
                else:
                    value = ''.join(li.xpath('./text()')).strip()

                journal_info[label_text] = value

        # 提取期刊简介、获奖情况和收录情况
        section_data = {}
        sections = tree.xpath('//div[contains(@class, "info-main")]//div[@class="info-box"]')
        
        for section in sections:
            title = section.xpath('.//div[@class="title"]/h2/text()')
            

            if title:  
                key = title[0].strip()  # 动态提取键
                
                # 特殊处理“期刊简介”
                if key == "期刊简介":
                    content = section.xpath('.//div[@class="info-content"]/p/text()')
                    if content:
                        content = content[0].strip()
                    else:
                        content = ""
                else:
                    content_list = section.xpath('.//div[@class="info-content"]//ul/li/text()')
                    content = [item.strip() for item in content_list]  

                section_data[key] = content  

        return {
            "期刊信息": journal_info,
            **section_data  # 合并期刊信息和各个动态提取的部分
        }


    @staticmethod
    def get_md5(value):
        md5_hash = hashlib.md5(str(value).encode('utf-8')).hexdigest()
        return md5_hash

    def save_journal_info(self, item):
        md5_hash = self.get_md5(item)       
        result = self.redis_client.sadd('reg_journal:filter', md5_hash)
        if result:
            self.collection.insert_one(item)
            print('数据插入成功:', item)
        else:
            print('数据重复...')

    def close_spider(self):
        print("closing db...")
        self.redis_client.close()
        self.mongo_client.close()

    def reach_end(self, response):
        tree = etree.HTML(response.text)
        sign = tree.xpath('//div[@class="no-data"]')
        if sign:
            print("all data collected")
            return True
        
    def collect_all_data(self):
        page_num = 1
        self.get_cookie()

        with ThreadPoolExecutor(max_workers=8) as executor: 
            while True:
                response = self.fetch_level_one_data(page_num)
                
                if self.reach_end(response):
                    break
                
                journal_links = self.parse_level_one(response)

                futures = {executor.submit(self.fetch_and_save, journal_name, summary_url): journal_name for journal_name, summary_url in journal_links}
                
                for future in as_completed(futures):
                    journal_name = futures[future]
                    try:
                        future.result()  
                        print(f"Successfully processed {journal_name}")
                    except Exception as exc:
                        print(f"{journal_name} generated an exception: {exc}")

                page_num += 1  

        self.close_spider()
        

    def fetch_and_save(self, journal_name, summary_url):
        detail_response = self.fetch_detail(summary_url)
        detail_data = self.parse_detail_page(detail_response)
        
        journal_data = {
            "期刊名称": journal_name,
            "期刊详情": detail_data
        }
        self.save_journal_info(journal_data)


if __name__ == "__main__":
    qikan_crawler = CnJournal()
    qikan_crawler.collect_all_data()
