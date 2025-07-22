# SQL DB LLM Agent System

자연어로 MS-SQL 및 SAP HANA DB에 질의하고, 쿼리 결과를 표, 자연어 요약, 또는 AI 기반 파이썬 리포트로 얻을 수 있는 웹 기반 LLM 에이전트 서비스입니다.

## 기능

- 자연어를 SQL로 변환
- MS-SQL 및 SAP HANA DB 지원
- 쿼리 결과의 자연어 요약
- 파이썬 기반 데이터 분석 및 시각화
- RAG 시스템을 통한 키워드 기반 검색
- 쿼리 이력 관리 및 공유

## 시작하기

### 필수 조건

- Node.js 16.x 이상
- Python 3.9 이상
- MS-SQL Server 2012 이상 또는 SAP HANA 1.0 이상

### 설치

```bash
# 백엔드 설치
cd backend
pip install -r requirements.txt

# 프론트엔드 설치
cd ../frontend
npm install
```

### 실행

```bash
# 백엔드 실행
cd backend
uvicorn main:app --reload

# 프론트엔드 실행
cd ../frontend
npm start
```

## 프로젝트 구조

```
sql_agent/
├── backend/           # FastAPI 백엔드
│   ├── api/           # API 엔드포인트
│   ├── core/          # 핵심 기능 및 설정
│   ├── db/            # DB 커넥터
│   ├── llm/           # LLM 서비스
│   ├── models/        # 데이터 모델
│   ├── rag/           # RAG 시스템
│   ├── services/      # 비즈니스 로직
│   ├── utils/         # 유틸리티 함수
│   └── main.py        # 애플리케이션 진입점
├── frontend/          # React 프론트엔드
│   ├── public/        # 정적 파일
│   ├── src/           # 소스 코드
│   │   ├── components/# UI 컴포넌트
│   │   ├── hooks/     # React 훅
│   │   ├── pages/     # 페이지 컴포넌트
│   │   ├── services/  # API 클라이언트
│   │   ├── store/     # 상태 관리
│   │   ├── utils/     # 유틸리티 함수
│   │   └── App.tsx    # 루트 컴포넌트
│   └── package.json   # 의존성 정의
└── README.md          # 프로젝트 문서
```