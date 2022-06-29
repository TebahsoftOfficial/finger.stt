# Speech Recognition Managment Service - finger.stt
finger.stt 는 음성인식 대화 서비스로서 인식된 음성으로 부터 다음과 같은 서비스를 제공하는 것을 목표로 한다.
- 대화 전사 기능
- 대화 분석 기능
- 단어 분석 기능
- 대화 편집 기능
- 축어록 생성 기능
- 화자 추가 및 편집 기능

## Installation
- Github에서 소스 코드 가져오기
명령창 실행 ( Win + R 실행 cmd 입력 )
```
> mkdir github
> cd github
> git clone https://github.com/TebahSoft/finger.stt.git
```

- 가상환경 설치
```
> cd finger.stt
> python -m venv ./fvenv
```

- 가상환경 활성화
```
> fvenv\Scripts\activate
```

- 패키지 설치
```
> pip install -r requirements.txt
```

- fingerai 폴더에 settings.py 파일 작성

- .envs 파일에 각종 key 정보 

- MySQL 설치 및 데이터베이스 생성 
[[Maria DB](https://mariadb.org/download/?t=mariadb&p=mariadb&r=10.9.1&os=windows&cpu=x86_64&pkg=msi&m=yongbok)]

- 데이터베이스 테이블 생성 및 작성
```
> python manage.py makemigrations
> python manage.py migrate
```

- superuser 생성
```
> python manage.py createsuperuser
```

- Runserver 실행 
```
> python manage.py runsslserver --certificate test_django.crt --key test_django.key 0.0.0.0:443
```

- SSL 설치 및 .key .crt 파일 생성 방법
[[OpenSSL 다운로드](http://slproweb.com/products/Win32OpenSSL.html)]
```
//key 파일 생성
> openssl genrsa 2048 > django.key
//key 파일 이용하여 crt 파일 생성
> openssl req -new -x509 -nodes -sha256 -days 365 -key django.key > django.crt
```

- 카카오톡에서 App ID , Secret 생성 
```
> https://developers.kakao.com/console/app 접속 후
> "내 애플리케이션" -> "애플리케이션 추가하기" 클릭 후 애플리케이션 작성
> 작성된 앱 클릭 -> 요약정보 -> "REST API 키"를 복사하여 Social Accounts의 "client id"에 입력
> 제품설정 -> 카카오 로그인 -> 보안 -> "Client Secret"-> "코드"를 복사하여 Social Accounts의 "Secret key"에 입력
```

- Social Accounts 설정 (카카오 로그인 연동)  
```
> 웹브라우저(chrome)에서 admin 페이지 접속
> https://127.0.0.1/admin 
> 우측 하단 "SITES"->"Sites" 선택
> 
> 좌측 하단 "Social accounts" -> "Social application" 메뉴 선택 
> 우측 상단 "ADD SOCIAL APPLICARION" 선택 => "Add Site" 클릭
> "Domain name: 127.0.0.1",  "display name:finger.stt"  입력
> 
> provider: kakao 선택
> client id : 카카오에서 App ID 생성 후 입력
> Secret key : 카카오에서 API Secret 생성 후 입력
> Available sites 에서 127.0.0.1 선택
```

- ".env" 파일 작성
```
# manage.py 와 같은 경로에 작성
# 각종 key, id 정보를 환경변수로 작성 저장
> DJANGO_KEY= Django key
> DB_NAME = MySQL 데이터베이스 네임
> DB_USER=MySQL 아이디
> DB_PWD=MySQL 암호
> CLOVA_INVOKE_URL=clova speech invoke url
> CLOVA_SECRET=clova speech secret
> NAVER_APIKEY_ID=naver api key, id
> NAVER_APIKEY=naver api id
> STORE_ACC_KEY=naver object storage access key
> STORE_SEC_KEY=naver object storage secret key
```


