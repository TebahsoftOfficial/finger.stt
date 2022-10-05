import requests
import json
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class ClovaSentimental:
    # Clova sentimental invoke URL
    invoke_url = 'https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze'

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


    def req_url(self, scont):
        self.set_secret()
        request_body = {
            'content': scont,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'Content-Type': 'application/json;UTF-8',

            'X-NCP-APIGW-API-KEY-ID': self.key_id,
            'X-NCP-APIGW-API-KEY': self.key
        }
        return requests.post(headers=headers,
                             url=self.invoke_url,
                             data=json.dumps(request_body).encode('UTF-8'))

if __name__ == '__main__':
    k= ClovaSentimental()
    res = k.req_url(scont="싸늘하다. 가슴에 비수가 날아와 꽂힌다.")

    #get_data = json.dumps(res.text)  #dic to json은 string 형태
    get_data = json.loads(res.text)  # json to dict
    a=get_data['document']['sentiment']
    print(get_data)
