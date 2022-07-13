# Speech Recognition Managment Service - finger.stt
finger.stt 는 음성인식 대화 서비스로서 인식된 음성으로 부터 다음과 같은 서비스를 제공하는 것을 목표로 한다.
- 대화 전사 기능
- 대화 분석 기능
- 단어 분석 기능
- 대화 편집 기능
- 화자 추가 및 편집 기능

![fingerstt01](https://user-images.githubusercontent.com/88182481/176337441-c43cf729-5124-400a-ab62-b18c18585fa4.png)

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
(1) 또는 (2) 방법 선택
> cd finger.stt
(1)
> conda create -n finger_venv python=3.8.10
(2)
> python -m venv ./fvenv
```

- 가상환경 활성화
```
(1)
> conda activate  finger_venv
(2)
> fvenv\Scripts\activate
```

- 패키지 설치
```
> pip install -r requirements.txt
> pip install boto3==1.6.19
> pip install python-dateutil==2.8.2
```

- fingerai 폴더에 settings.py 파일 작성
```
import os
from pathlib import Path
#from decouple import config
import os
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)        
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))            

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_KEY') 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
#DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = ['localhost','127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'crispy_forms',
    "crispy_bootstrap5",
    'markdownx',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.kakao',
    'interviews',
    'start_pages',
    'mathfilters',
    'sslserver',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',      
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fingerai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'fingerai.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'), 
        "USER": env('DB_USER'), 
        "PASSWORD": env('DB_PWD'), 
        "HOST": "127.0.0.1",
        "PORT": '3306',

    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
#CRISPY_ALLOWED_TEMPLATE_PACKS = "uni_form"
#CRISPY_TEMPLATE_PACK = "uni_form"

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_LOGOUT_ON_GET = True     # disable intermediate log out
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/' #'/interviews/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/' #'/interviews/'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
if DEBUG == True:
    #STATICFILES_DIRS = [BASE_DIR / 'static', os.path.join(BASE_DIR, 'interviews', 'static')]
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'), os.path.join(BASE_DIR, 'interviews', 'static')]
    #STATICFILES_DIRS = os.path.join(BASE_DIR, 'static')
    STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]
#else:

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '_media')
#DEFAULT_FILE_STORAGE = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

X_FRAME_OPTIONS = 'SAMEORIGIN'
```

- .envs 파일 작성 및 각종 key 정보
- manage.py 와 같은 경로에 작성
- 각종 key, id 정보를 환경변수로 작성 저장
```
DJANGO_KEY= Django key
DB_NAME = MySQL 데이터베이스 네임
DB_USER=MySQL 아이디
DB_PWD=MySQL 암호
CLOVA_INVOKE_URL=clova speech invoke url
CLOVA_SECRET=clova speech secret
NAVER_APIKEY_ID=naver api key, id
NAVER_APIKEY=naver api id
STORE_ACC_KEY=naver object storage access key
STORE_SEC_KEY=naver object storage secret key
```


- MySQL 설치 및 데이터베이스 생성 
[[Maria DB](https://mariadb.org/download/?t=mariadb&p=mariadb&r=10.9.1&os=windows&cpu=x86_64&pkg=msi&m=yongbok)]

- 데이터베이스 테이블 생성 및 작성
```
> python manage.py makemigrations
   # 아래와 같은 에러 발생시
   # importError: DLL load failed while importing win32api: 지정된 모듈을 찾을 수 없습니다
    > conda install -c anaconda pywin32   로 해결
> python manage.py migrate
```

- superuser 생성
```
> python manage.py createsuperuser
```

- Runserver 실행 
```
python manage.py runsslserver --certificate test_django.crt --key test_django.key 0.0.0.0:443
```

- SSL 설치 및 .key .crt 파일 생성 방법
[[OpenSSL 다운로드](http://slproweb.com/products/Win32OpenSSL.html)]
```
//key 파일 생성
openssl genrsa 2048 > test_django.key
//key 파일 이용하여 crt 파일 생성
openssl req -new -x509 -nodes -sha256 -days 365 -key test_django.key > test_django.crt
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




