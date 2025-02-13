import requests
import json
import pymongo
import redis
import hashlib
import execjs
import re
import time
from typing import Dict, Any

class BwPurchase:
    headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,fr;q=0.8,en;q=0.7,zh-TW;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://qiye.obei.com.cn",
    "Pragma": "no-cache",
    "Referer": "https://qiye.obei.com.cn/web-zone/bwzy/procurement.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
   
}
    cookies = {}
    url = "https://qiye.obei.com.cn/web-zone/api/sys/zone/getPurchaseList"

    def __init__(self):
        self.mongo_client = pymongo.MongoClient(host='localhost', port=27017)
        self.collection = self.mongo_client['py_spider']['bwzy_purchase_info']
        self.redis_client = redis.Redis()

    @staticmethod
    def generate_cookie():
        with open("补环境getCookie.js", encoding='utf-8') as f:
            js_code = f.read()

        cookie_str = execjs.compile(js_code).call('getCookie')
        return cookie_str
    
    @staticmethod
    def parse_cookies(cookie_string: str) -> Dict[str, str]:
    
        cookie_dict = {}
        cookies = cookie_string.split('; ')    
        for cookie in cookies:     
            key_value = cookie.split('=')       
            if len(key_value) == 2:
                cookie_dict[key_value[0]] = key_value[1] 
        
        return cookie_dict

    @classmethod
    def get_cookies(cls) -> Dict[str, str]:
        """
        获取document.cookie
        更新key为HKIIUU9O618PPTHPM的cookie值
        """
        cookie_str = cls.generate_cookie()
        cookie_dict = cls.parse_cookies(cookie_str)
        cls.cookies["HKIIUU9O618PPTHPM"] = cookie_dict["HKIIUU9O618PPTHPM"]
    
        return cookie_dict

    @classmethod
    def format_initial_request(cls):
        
        cookie_dict = cls.get_cookies()
        csrfToken = cookie_dict["csrfToken"]
        cls.headers["x-csrf-token"] = csrfToken

        cls.cookies["HKIIUU9O618PPTHKM"] = cookie_dict["HKIIUU9O618PPTHKM"]
        cls.cookies["csrfToken"] = csrfToken
        
    @classmethod
    def update_params(cls):

        cls.format_initial_request()
        url = "https://qiye.obei.com.cn/web-zone/bwzy/procurement.html"
        response = requests.get(url, headers=cls.headers, cookies=cls.cookies)

        set_cookie_header = response.headers.get('Set-Cookie')
        print("set-cookie: ", set_cookie_header)
        if set_cookie_header:
            KM_cookie = set_cookie_header.split(";")[0]
            KM_value = KM_cookie.split("=")[1]
            print(KM_value)
            cls.cookies["HKIIUU9O618PPTHKM"] = KM_value
        
        else:
            print("set-cookie not found")

        match = re.search(r'"csrf":\s*"([^"]+)"', response.text)

        if match:
            csrf_value = match.group(1)
            print(f"CSRF Value: {csrf_value}")  
            cls.cookies["csrfToken"] = csrf_value
            cls.headers["x-csrf-token"] = csrf_value
        else:
            print("CSRF value not found.")
        
        cls.get_cookies()
        # 更新HKIIUU9O618PPTHPM

    @classmethod
    def get_response(cls, data):

        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(cls.url, headers=cls.headers, cookies=cls.cookies, data=data)
  
        return response

    def parse_purchase_data(self, purchase_list):
        
        for notice in purchase_list:
            item = dict()
            item['标题'] = notice['title']
            item['发布时间'] = notice['issueDate']
            item['寻源方式'] = notice['rfqMethod']

            self.save_purchase_info(item)

    @staticmethod
    def get_md5(value):
        md5_hash = hashlib.md5(str(value).encode('utf-8')).hexdigest()
        return md5_hash

    def save_purchase_info(self, item):
        md5_hash = self.get_md5(item)
        
        result = self.redis_client.sadd('notice:filter', md5_hash)
        if result:
            self.collection.insert_one(item)
            print('数据插入成功:', item)
        else:
            print('数据重复...')

    def close_spider(self):
        print('数据库即将关闭...')
        self.redis_client.close()
        self.mongo_client.close()

    def main(self):

        self.format_initial_request()
        for page in range(1, 11):
            data = {
                "code": "bwzy",
                "noticeType": "1",
                "pageNum": page,
                "pageSize": 10,
                "pageFlag": "addSelect",
                "sidx": "issueDate",
                "sord": "desc"
            }
     
            response = self.get_response(data)

            if response.status_code != 200 or type(response.json()['data']) != list:
                print(f"Request failed with status code: {response.status_code}. Updating params...")
                time.sleep(1)  
                self.update_params()  
                time.sleep(1)  

                response = self.get_response(data)
        

            item_list = response.json().get('data', [])
            print(f"Items on page {page}: {item_list}")
            
            self.parse_purchase_data(item_list)

            if page % 2 == 0 and page < 10:
                print("Updating parameters after every 2 pages...")
                self.update_params()  
                time.sleep(1)  
           
        
        self.close_spider()

if __name__ == '__main__':
    bw_purchase = BwPurchase()
    bw_purchase.main()
