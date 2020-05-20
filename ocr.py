'''
@Description: Capture than OCR - Quicker for Windows - Online OCR
@version: 1.0
@Author: Chandler Lu
@Date: 2020-03-07 17:38:10
@LastEditTime: 2020-03-08 14:34:03
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import statistics
import uuid
import io

import json
import re
import requests

import hashlib
import random
import string
from base64 import b64encode
from urllib import parse

import time
import TencentYoutuyun
import latex2mathml.converter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

OCR_SELECT = int(sys.argv[1])
PIC_PATH = sys.argv[2]
try:
    MODE = sys.argv[3]
    TYPE = sys.argv[4]
except:
    MODE = 'formula'
    TYPE = 'latex'
# Key
with open("./API_Key.json", "r") as json_file:
    api_key = json.load(json_file)

# Error Declare
def declare_network_error():
    print('Network connection refused!', end='')
    sys.exit(0)


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64

# 百度ocr
def baidu_ocr(pic_path, mode='formula', type='latex'):
    def request_baidu_token():
        try:
            api_message = requests.post(BAIDU_GET_TOKEN_URL)
            if api_message:
                with open("./baidu_api_token.json", "w") as json_file:
                    json.dump(api_message.json(), json_file)
                token = api_message.json()['access_token']
                return token
        except requests.exceptions.ConnectionError as e:
            print(e)
            declare_network_error()
    def return_baidu_token():
        if ((not os.path.exists('./baidu_api_token.json'))
                or (int(time.time() - os.stat("./baidu_api_token.json").st_mtime) >= 259200)):
            return request_baidu_token()
        else:
            with open("./baidu_api_token.json", 'r') as json_file:
                api_message_json = json.load(json_file)
                if 'access_token' in api_message_json:
                    return api_message_json.get('access_token')
                else:
                    return request_baidu_token()

    # 初始化

    BAIDU_API_KEY = api_key['baidu_api_key']
    BAIDU_SECRET_KEY = api_key['baidu_secret_key']
    BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
    BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'
    baidu_formula_ocr_api = 'https://aip.baidubce.com/rest/2.0/ocr/v1/formula'
    if (os.path.getsize(pic_path) <= 4194304):
        try:
            if mode == 'formula':
                url = baidu_formula_ocr_api
            response = requests.post(
                url,
                params={
                    "access_token": return_baidu_token(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "image": convert_image_base64(pic_path),
                },
                verify=False
            )
            if (response.status_code == 200):
                # print(response.json())
                output_formula('baidu_ocr',response.json(), type)
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError as e:
            print(e)
            declare_network_error()
    else:
        print('Too large!')
    

def tencent_youtu_ocr(pic_path, mode='formula', type='latex'):
    youtu_appid = api_key['youtu_appid']
    youtu_secret_id = api_key['youtu_secret_id']
    youtu_secret_key = api_key['youtu_secret_key']
    youtu_userid = api_key['youtu_userid']

    end_point = TencentYoutuyun.conf.API_YOUTU_END_POINT
    youtu = TencentYoutuyun.YouTu(youtu_appid, youtu_secret_id, youtu_secret_key, youtu_userid, end_point)
    ret = youtu.formularocr(pic_path)
    output_formula('tencent_youtu_ocr', ret["items"], type)


def xue_er_si_ocr(pic_path, mode='formula', type='latex'):
    generalocr_api = 'http://openapiai.xueersi.com/v1/api/img/ocr/general'
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'cache-control': "no-cache"
    }
    data = {
        'app_key': api_key['xue_er_si_appkey'],
        'img': convert_image_base64(pic_path),
        'img_type': 'base64'
    }
    if os.path.getsize(pic_path) <= 4194304:
        try:
            r = requests.post(generalocr_api, headers=headers, data=data)
            if r.status_code == 200:
                reponse_json = r.json()
                output_formula('xue_er_si_ocr', reponse_json, type)
            else:
                print('请求返回码不为200，出错！')
        except:
            print('无法建立连接')
    else:
        print('图片超过4M')


def youdao_ocr(pic_path, mode='formula', type='latex'):

    def truncate(q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


    def encrypt(signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()


    def do_request(data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(YOUDAO_URL, data=data, headers=headers)

    YOUDAO_URL = 'https://openapi.youdao.com/ocr_formula'
    APP_KEY = api_key['youdao_api_key']
    APP_SECRET = api_key['youdao_api_secret']

    f = open(pic_path, 'rb')  # 二进制方式打开图文件
    q = convert_image_base64(pic_path)
    curtime = str(int(time.time()))
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data = {
        "detectType": "10012",
        "imageType": "1",
        "langType": "auto",
        "img": q,
        "docType": "json",
        "signType": "v3",
        "curtime": curtime,
        "appKey": APP_KEY,
        "salt": salt,
        "sign": sign,
    }

    response = do_request(data)
    output_formula('youdao_ocr', response.json(), type)

def mathpix_ocr(pic_path, mode='formula', type='latex'):
    
    mathpix_app_id = api_key['mathpix_app_id']
    mathpix_app_key = api_key['mathpix_app_key']
    url = "https://api.mathpix.com/v3/text"

    image_uri = "data:image/jpg;base64," + convert_image_base64(pic_path)
    try:
        r = requests.post(url,
                        data=json.dumps({
                            "src": image_uri,
                            "formats": ["latex","data"],
                            "data_options": {
                                "include_latex": True,
                                "include_mathml": True
                            }
                        }),
                        headers={
                            "app_id": mathpix_app_id,
                            "app_key": mathpix_app_key,
                            "Content-type": "application/json"
                        }
                        )
    except:
        print('连接建立出错')
    output_formula('mathpix_ocr', r.json(), type)

# 输出结果
def output_formula(which_api, result_json, type='latex'):
    response_json = result_json
    # print(response_json)
    handled_text = ''
    if which_api == 'tencent_youtu_ocr':
        for index in range(len(response_json)):
            handled_text = response_json[index]['itemstring']
    elif which_api == 'xue_er_si_ocr':
        if response_json['code'] == 0:
            handled_text = '\n'.join(response_json["data"]["content"])
        else:
            print('错误代码：' + response_json['code'] + '\n错误信息：' + response_json['msg'])
    elif which_api == 'baidu_ocr':
        for text in response_json['words_result']:
            handled_text += re.sub(r'(^| )([^一-龥]+) ', r'$\2$', text['words']) + '\n'
    elif which_api == 'youdao_ocr':
        for line in response_json['Result']['regions'][0]['lines']:
            for word in line:
                if word['type'] == 'formula':
                    handled_text += '$' + word['text'] + '$'
                else:
                    handled_text += word['text']
            handled_text += '\n'
    elif which_api == 'mathpix_ocr':
        for item in response_json['data']:
            if item['type'] == type:
                #handled_text += '$' + item['value'].replace('\u2212','-').replace('\u22c5', '·') + '$\n'
                print(item['value'].replace('\u2212','-').replace('\u22c5', '·') + '\n***分隔符***\n', end='')
        return
    # 确定输出形式
    handled_text.replace('\u2212','-').replace('\u22c5', '·')
    if type == 'latex':
        print(handled_text)
    elif type == 'mathml':
        # 去除预处理中加上的$
        handled_text = handled_text.replace('$', '')
        print(latex2mathml.converter.convert(handled_text))
    elif type == 'all':
        print(handled_text)
        # 去除预处理中加上的$
        handled_text = handled_text.replace('$', '')
        print(latex2mathml.converter.convert(handled_text))



def remove_pic(pic_path):
    os.remove(pic_path)


if __name__ == "__main__":
    '''
    1: 百度公式
    2: 腾讯优图
    3: 学而思公式
    4: 有道公式
    5: Mathpix
    '''
    if OCR_SELECT == 1:
        baidu_ocr(PIC_PATH, MODE, TYPE)
    elif OCR_SELECT == 2:
        tencent_youtu_ocr(PIC_PATH, MODE, TYPE)
    elif OCR_SELECT == 3:
        xue_er_si_ocr(PIC_PATH, MODE, TYPE)
    elif OCR_SELECT == 4:
        youdao_ocr(PIC_PATH, MODE, TYPE)
    elif OCR_SELECT == 5:
        mathpix_ocr(PIC_PATH, MODE, TYPE)
    remove_pic(PIC_PATH)
