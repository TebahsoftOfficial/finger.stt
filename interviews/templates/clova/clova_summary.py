# -*- coding: utf-8 -*-
import requests
import json
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class ClovaSummary:
    invoke_url = 'https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize'

    key_id ='' 
    key =''

    def set_secret(self):
        env = environ.Env(
            # set casting, default value
            DEBUG=(bool, False)
        )        
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))            
        self.key_id = env('NAVER_APIKEY_ID')
        self.key = env('NAVER_APIKEY')

    def req_url(self, document, option):
        self.set_secret()
        request_body = {
            'document': document,
            'option': option,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'Content-Type': 'application/json;UTF-8',
            # 주계정
            'X-NCP-APIGW-API-KEY-ID': self.key_id,
            'X-NCP-APIGW-API-KEY': self.key            

        }
        return requests.post(headers=headers,
                             url=self.invoke_url,
                             data=json.dumps(request_body).encode('UTF-8'))

if __name__ == '__main__':

    doc = {'content':''}
    opt = {'language':'ko','model':'general','tone':1,'summaryCount':5}

    doc['content'] = "간편송금 이용금액이 하루 평균 2000억원을 넘어섰다. 한국은행이 17일 발표한 '2019년 상반기중 전자지급서비스 이용 현황'에 따르면 올해 상반기 간편송금서비스 이용금액(일평균)은 지난해 하반기 대비 60.7% 증가한 2005억원으로 집계됐다. 같은 기간 이용건수(일평균)는 34.8% 늘어난 218만건이었다. 간편 송금 시장에는 선불전자지급서비스를 제공하는 전자금융업자와 금융기관 등이 참여하고 있다. 이용금액은 전자금융업자가 하루평균 1879억원, 금융기관이 126억원이었다. 한은은 카카오페이, 토스 등 간편송금 서비스를 제공하는 업체 간 경쟁이 심화되면서 이용규모가 크게 확대됐다고 분석했다. 국회 정무위원회 소속 바른미래당 유의동 의원에 따르면 카카오페이, 토스 등 선불전자지급서비스 제공업체는 지난해 마케팅 비용으로 1000억원 이상을 지출했다. 마케팅 비용 지출규모는 카카오페이가 491억원, 비바리퍼블리카(토스)가 134억원 등 순으로 많았다."
    k = ClovaSummary()
    res = k.req_url(document=doc, option=opt)
    #f = open("csummary_test.txt", "w")
    #get_data = json.dumps(res.text)  #dic to json은 string 형태
    get_data = json.loads(res.text)  # json to dict
    print(k.key_id)
    print(k.key)
    print(get_data)
    a = get_data['summary']
    print(a)
    #f.write(a)
    #f.close()