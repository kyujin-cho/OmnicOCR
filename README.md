# 전적옴닉 (트위치 스트리머 배그 전적 자동인식 스크립트)
## 요구사항
- Tesseract 3.05 버전, 혹은 그 이상 
- Python3
- dependencies.txt의 라이브러리들 (`pip3 install -r dependencies.txt`로 설치가능 )
     
## 제약사항 
- 한글 배그 UI에 최적화된 스크립트입니다. 영문 혹은 기타 언어의 배그 방송에 적용하시려면 등수 및 시작 버튼 좌표 조정이 필요할 수 있습니다. 
- 전체 등수 파악이 불가합니다. 엘린 팬티 팔아먹은 새끼들이 UI 업데이트 안해주면 방법이 없습니다.
- 듀오/스쿼드 구분을 지원하지 않습니다. 언제 업데이트 할진 딩요 애미도 모릅니다.
- 버그가 종니 많습니다.
## 사용방법
1-1. 자동설치
- install.sh를 실행합니다. 근데 테스트 안해봐서 안될 가능성이 높습니다.
1-2. 수동설치
    1. settings.py 파일을 만듭니다. 내용은 다음과 같아야 합니다.
    ```
    host='<DB Host>'
    user='<DB ID>'
    password='<DB PW>'
    db='<DB Name>'
    ClientID = '<Twitch API Client ID>'

    streamers = [<List of twitch streamers>]
    ```
    2. 다음과 같이 DB를 구성합니다.
    ```
    CREATE TABLE `score` (
    `index_` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `streamer_id` varchar(45) NOT NULL,
    `series` int(10) unsigned NOT NULL,
    `rank` int(10) NOT NULL,
    `type` varchar(20) DEFAULT NULL,
    PRIMARY KEY (`index_`)
    ) ENGINE=InnoDB AUTO_INCREMENT=92 DEFAULT CHARSET=utf8;
    ```
    ```
    CREATE TABLE `broadcast` (
    `series` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `streamer_id` varchar(45) NOT NULL,
    `start` datetime NOT NULL,
    `end` datetime DEFAULT NULL,
    PRIMARY KEY (`series`)
    ) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8;
    ```
    Broadcast 테이블은 방송 시작과 끝 정보가 들어갈 테이블입니다.
    3. 실행합니다.
