# SQL DB LLM Agent Backend

자연어로 SQL 데이터베이스에 질의하고 결과를 분석하는 LLM 기반 에이전트 시스템의 백엔드 서버입니다.

## 기술 스택

- FastAPI: 고성능 웹 프레임워크
- SQLAlchemy: SQL 툴킷 및 ORM
- PyODBC/PyMSSQL: MS-SQL 연결 드라이버
- HDBCLI: SAP HANA 연결 드라이버
- OpenAI API: LLM 서비스 연동
- Pandas/Matplotlib/Plotly: 데이터 분석 및 시각화

## 설치 및 실행

### 1. 가상 환경 설정

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (Linux/Mac)
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다.

```bash
cp .env.example .env
```

### 4. 데이터베이스 초기화

```bash
python -m db.init_db
```

### 5. 서버 실행

```bash
uvicorn main:app --reload
```

서버가 실행되면 `http://localhost:8000/api/docs`에서 API 문서를 확인할 수 있습니다.

## 프로젝트 구조

```
backend/
├── api/                # API 라우터
│   ├── auth.py         # 인증 관련 API
│   ├── database.py     # 데이터베이스 연결 관련 API
│   ├── query.py        # 쿼리 실행 관련 API
│   ├── result.py       # 결과 처리 관련 API
│   └── admin.py        # 관리자 기능 API
├── core/               # 핵심 기능
│   ├── config.py       # 설정 관리
│   ├── dependencies.py # 의존성 함수
│   └── middleware.py   # 미들웨어
├── db/                 # 데이터베이스 관련
│   ├── session.py      # DB 세션 관리
│   ├── base_model.py   # 기본 모델 클래스
│   └── init_db.py      # DB 초기화 스크립트
├── llm/                # LLM 서비스 관련
├── models/             # 데이터 모델
│   ├── user.py         # 사용자 모델
│   ├── database.py     # 데이터베이스 모델
│   ├── query.py        # 쿼리 모델
│   └── rbac.py         # 권한 관리 모델
├── rag/                # RAG 시스템 관련
├── services/           # 비즈니스 로직
├── utils/              # 유틸리티 함수
├── main.py             # 애플리케이션 진입점
└── requirements.txt    # 의존성 목록
```
