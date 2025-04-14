프로그램 실행 가이드
===================

필요 사항
--------
1. Python 3.x 설치
   - https://www.python.org/downloads/ 에서 최신 Python 설치

설치 방법
--------
1. 가상환경 생성 및 활성화:
   python -m venv venv
   - Windows: venv\Scripts\activate
   - Linux/Mac: source venv/bin/activate

2. 필요한 패키지 설치:
   pip install -r requirements.txt

실행 방법
--------
1. 프로그램 실행:
   python hwang.py

2. 웹 브라우저가 자동으로 열리면서 인터페이스가 표시됩니다
   (기본적으로 http://localhost:7860 에서 접속 가능)

사용 방법
--------
1. 시장 경쟁도 설정 (0.0 ~ 1.0)
2. 초기 임금 입력 (원 단위)
3. 시뮬레이션 횟수 설정 (1 ~ 10회)
4. Submit 버튼 클릭
5. 결과 확인

버전 정보
--------
Version 1.0
최종 수정일: [날짜]

문제 해결
--------
- "python이 인식되지 않는 경우":
  Python이 PATH에 추가되지 않은 것입니다.
  Python을 재설치하고 "Add Python to PATH" 옵션을 체크해주세요.

- 프로그램 실행 중 오류 발생 시:
  화면에 표시되는 에러 메시지를 확인하고 담당자에게 문의해주세요.

시뮬레이션 매개변수 설명
-------------------
- 시장 경쟁도 (매개변수 1)
  - 범위: 0.0 ~ 1.0
  - 의미: 시장의 경쟁 강도를 나타냄
  - 0에 가까울수록 낮은 경쟁, 1에 가까울수록 높은 경쟁

- 초기 임금 (매개변수 2)
  - 단위: 원
  - 예시: 3000000 (300만원)
  - 의미: 노동자의 초기 기대 임금

연락처
-----
문의사항이나 기술지원이 필요한 경우 아래로 연락주세요:
[담당자 연락처 정보]

가상환경 설정 방법 (권장)
--------------------
1. 가상환경 생성:
   python -m venv venv

2. 가상환경 활성화:
   - Windows:
     venv\Scripts\activate
   - Linux/Mac:
     source venv/bin/activate

3. 필요한 패키지 설치:
   pip install -r requirements.txt

4. 프로그램 실행:
   python hwang.py

5. 사용 완료 후 가상환경 비활성화:
   deactivate 