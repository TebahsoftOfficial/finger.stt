# finger.stt
Speech Recognition Managment Service
----------------

finger.stt 는 음성인식 대화 서비스로서 인식된 음성으로 부터 다음과 같은 서비스를 제공하는 것을 목표로 한다.
- 대화 전사 기능
- 대화 분석 기능
- 단어 분석 기능
- 대화 편집 기능
- 축어록 생성 기능
- 화자 추가 및 편집 기능

Installation
-----------------------------
- Github에서 소스 코드 가져오기
명령창 실행 ( Win + R 실행 cmd 입력 )
> mkdir github
> cd github
> git clone https://github.com/TebahSoft/finger.stt.git

- 가상환경 설치
> cd finger.stt
> python -m venv ./fvenv

- 가상환경 활성화
> fvenv\Scripts\activate

- 패키지 설치
> pip install -r requirements.txt
