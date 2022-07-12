# https://developers.vito.ai/docs/stt-file/

import requests
import json
import time
import webbrowser
import urllib
import boto3

#from threading import Timer,Thread,Event

#token의 만료 기간은 6시간입니다. 주기적으로 token이 갱신될 수 있도록 /v1/authenticate 을 통해 token을 갱신해야 합니다.
# 인증 토큰 요청
'''
{
  // access token
  access_token?: string
  // expiration in unixtimestamp
  expire_at?: integer
}
'''

def vito_auth():

    resp = requests.post(
        'https://openapi.vito.ai/v1/authenticate',
        data={'client_id': "MXRzJ6bhk90kCV4tXgEd",
            'client_secret': "nT8ORQin8dzHh61JBaO1tW4gN4ea-lWU7eDbNV0C"}
    )
    resp.raise_for_status()
    ret = resp.json()    # json => dict
    print(ret)
    return ret['access_token']



def vito_stt_url_req(token, file):
    r=requests.get(file)    ##### 동기 처리 검토!!!!
    config = {
    "diarization": {
        "use_ars": False,
        "use_verification": False
    },
    "use_multi_channel": False
    }
    resp = requests.post(
        'https://openapi.vito.ai/v1/transcribe',
        headers={'Authorization': 'bearer '+token},
        data={'config': json.dumps(config)},
        files = {'file': r.content }
        #files = {'file': webbrowser.open(file)}
        #files={'file': open(file, 'rb')}
    )
    resp.raise_for_status()
    ret = resp.json()
    print(ret)
    return ret['id']

def vito_stt_file_req(token, file):
    config = {
    "diarization": {
        "use_ars": False,
        "use_verification": False
    },
    "use_multi_channel": False
    }
    resp = requests.post(
        'https://openapi.vito.ai/v1/transcribe',
        headers={'Authorization': 'bearer '+token},
        data={'config': json.dumps(config)},
        files={'file': open(file, 'rb')}
    )
    resp.raise_for_status()
    ret = resp.json()
    print(ret)
    return ret['id']    


def vito_stt_res(token, id):
    resp = requests.get(
        'https://openapi.vito.ai/v1/transcribe/'+id,
        headers={'Authorization': 'bearer '+token},
    )
    resp.raise_for_status()
    return resp.json() 


def vito_check(token, id):
    res = ''
    while True:
        res = vito_stt_res(token, id)
        if res['status']=='completed':
            break;
        print(res['status'])
        time.sleep(2)
    return res

def vito_auto_process(file):
    acc_token = vito_auth()   
    print(f"{file}")
    if file.find("http") == -1:
        print("File Vito")
        id = vito_stt_file_req(acc_token, file)
    else:
        print("URL Vito")
        id = vito_stt_url_req(acc_token, file)
    res = vito_check(acc_token, id)
    print(res['results'])
    return res

def create_presigned_url(bucket_name, object_name, expiration=3600):
    try:
        response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        print(e)
        return None

    return response    

if __name__ == '__main__':
    #url = "https://kr.object.ncloudstorage.com/fingerai-dev/sample-folder/measure1.mp3?AWSAccessKeyId=bDh7dxf72aJw2F66ayAn&Signature=mmUSOSuMYlf4mS35BBTMy4YbPBU%3D&Expires=1657103757"
    #file = './measure1.mp3'
    service_name = 's3'
    endpoint_url = 'https://kr.object.ncloudstorage.com'
    region_name = 'kr-standard'
    access_key = 'bDh7dxf72aJw2F66ayAn'
    secret_key = 'YpxdN9V1KRaX1xmkCNj5kBu277IVGf9jzJKgtY1b'

    s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)

    bucket_name = 'fingerai-dev'

    object_name = 'sample-folder/measure1.mp3'

    url = create_presigned_url(s3, bucket_name, object_name)    
    vito_auto_process(url)

