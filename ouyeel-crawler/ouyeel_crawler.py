import redis
import pymongo
import requests
import execjs
from lxml import etree
import json
import hashlib
from retrying import retry
import time
import json
from requests.exceptions import RequestException


class OuYeel:
    def __init__(self):
        self.mongo_client = pymongo.MongoClient()
        self.collection = self.mongo_client['py_spider']['oy_product']
        self.session = requests.Session()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        
        self.url = "https://www.ouyeel.com/search-ng/queryResource/index"
        self.cookies = {}
        
        self.redis_client = redis.Redis()

    def get_cookie(self):

        response = self.session.get(self.url, headers=self.headers)
        tree = etree.HTML(response.content.decode()) 
        
        content = tree.xpath("//meta[2]/@content")[0]       
        ts_code_str = tree.xpath("//script[1]/text()")[0]
        js_file_src = tree.xpath("//script[2]/@src")[0]
        js_file_url = "https://www.ouyeel.com" + js_file_src
        
        response = self.session.get(js_file_url, headers=self.headers)
        # print(response)
        iife_code = response.text
        with open("外链.js", 'w') as f:
            f.write(iife_code)

        with open("variable_ts.js", encoding='utf-8') as f:
            js_code = f.read().replace("content_value", content).replace('"ts_code_str"', ts_code_str)

        cookie = execjs.compile(js_code).call("getCookie")
        cookie = cookie.split(";")[0]
        self.cookies = {
            cookie.split('=')[0]: cookie.split('=')[1]
        }

    @staticmethod
    def format_data(page):

        data = {
            "criteriaJson": "{\"pageIndex\":%d,\"pageSize\":50,\"industryComponent\":null,\"channel\":null,\"productType\":null,\"sort\":null,\"warehouseCode\":null,\"key_search\":null,\"is_central\":null,\"searchField\":null,\"companyCode\":null,\"inquiryCategory\":null,\"inquirySpec\":null,\"provider\":null,\"packCodes\":null,\"shopCode\":null,\"steelFactory\":null,\"resourceIds\":null,\"jsonParam\":{},\"excludeShowSoldOut\":null}" % page
        }
        return data

    @retry(stop_max_attempt_number=5)
    def fetch_page_data(self, page):
        api_url = "https://www.ouyeel.com/search-ng/complexSearch/queryCombinationResult" # 详细版
        data = self.format_data(page)    
        response = self.session.post(api_url, headers=self.headers, cookies=self.cookies, data=data)
        if response.status_code == 200:
            return response

        else:
            time.sleep(2)
            self.get_cookie()
            print("cookie refreshed: ", self.cookies)
            raise RequestException(f"页面请求失败，状态码：{response.status_code}")

    def parse_data(self, response):

        product_list = response.json()["resultList"]
        for product in json.loads(product_list):

            item = dict()
            item["标题"] = " ".join([product["manufactureName"], product["qualityGradeName"], product["spec"], product["shopSign"]])
            item["价格"] = f'¥{product["publishPrice"]}/吨'
            item["地址"] = " | ".join([product["storeCityName"] if product["storeCityName"] else "", product["warehouseName"] if product["storeCityName"] else ""])
            # 测试
            # print(item)
            self.save_product(item)
            

    @staticmethod
    def get_md5(value):
        md5_hash = hashlib.md5(str(value).encode('utf-8')).hexdigest()
        return md5_hash

    def save_product(self, item):

        md5_hash = self.get_md5(item)       
        result = self.redis_client.sadd('oyproduct:filter', md5_hash)
        if result:
            self.collection.insert_one(item)
            print('数据插入成功:', item)
        else:
            print('数据重复...')
        

    def close_spider(self):
        print("closing db...")
        self.redis_client.close()
        self.mongo_client.close()

    def main(self):
        self.get_cookie()
        # 测试
        # response = self.fetch_page_data(1)
        # self.parse_data(response)
        for page in range(0,10):
            response = self.fetch_page_data(page)
            self.parse_data(response)

        self.close_spider()
      



if __name__ == "__main__":
    scrapy = OuYeel()
    scrapy.main()      

