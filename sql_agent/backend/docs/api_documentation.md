# SQL DB LLM Agent API 문서

## 개요

SQL DB LLM Agent API는 자연어로 SQL 데이터베이스에 질의하고 결과를 분석하는 LLM 기반 에이전트 시스템의 백엔드 API입니다. 이 문서는 API의 사용 방법, 엔드포인트, 요청/응답 형식, 오류 처리 등에 대한 정보를 제공합니다.

## 기본 정보

- **기본 URL**: `/api`
- **API 버전**: 0.1.0
- **문서 URL**: `/api/docs` (Swagger UI)
- **ReDoc URL**: `/api/redoc` (ReDoc)
- **OpenAPI 스펙**: `/api/openapi.json`

## 인증

API는 OAuth2 기반의 Bearer 토큰 인증을 사용합니다. 대부분의 엔드포인트는 인증이 필요합니다.

### 인증 흐름

1. `/api/auth/login` 엔드포인트를 통해 사용자 인증 정보(사용자명, 비밀번호)를 제출합니다.
2. 성공적으로 인증되면 액세스 토큰을 받습니다.
3. 이후 요청에서 `Authorization` 헤더에 `Bearer {token}` 형식으로 토큰을 포함시킵니다.

### 인증 예제

```bash
# 로그인 및 토큰 획득
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password"

# 토큰을 사용한 API 호출
curl -X GET "http://localhost:8000/api/db/list" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## API 엔드포인트 그룹

API는 다음과 같은 주요 엔드포인트 그룹으로 구성되어 있습니다:

1. [인증 API](#인증-api)
2. [데이터베이스 API](#데이터베이스-api)
3. [쿼리 API](#쿼리-api)
4. [결과 API](#결과-api)
5. [리포트 API](#리포트-api)
6. [이력 및 공유 API](#이력-및-공유-api)
7. [피드백 API](#피드백-api)
8. [관리자 API](#관리자-api)

각 API 그룹에 대한 자세한 설명은 해당 섹션을 참조하세요.
