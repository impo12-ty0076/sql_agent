# SQL DB LLM Agent API 문서

## 소개

SQL DB LLM Agent는 비전문가도 자연어로 MS-SQL 및 SAP HANA DB에 질의하고, 쿼리 결과를 표, 자연어 요약, 또는 AI 기반 파이썬 리포트(토글 방식)로 얻을 수 있는 웹 기반 LLM 에이전트 서비스입니다.

이 문서는 SQL DB LLM Agent API의 사용 방법, 엔드포인트, 요청/응답 형식, 오류 처리 등에 대한 정보를 제공합니다.

## 문서 구성

1. [API 개요](api_documentation.md) - API의 기본 정보 및 구조
2. [인증 API](auth_api.md) - 사용자 인증 및 세션 관리
3. [데이터베이스 API](database_api.md) - 데이터베이스 연결 및 스키마 조회
4. [쿼리 API](query_api.md) - 자연어 질의 처리 및 SQL 쿼리 실행
5. [결과 API](result_api.md) - 쿼리 결과 조회 및 분석
6. [이력 및 공유 API](history_api.md) - 쿼리 이력 관리 및 공유
7. [관리자 API](admin_api.md) - 사용자 관리, 정책 설정, 시스템 모니터링
8. [오류 코드 및 처리 방법](error_codes.md) - API 오류 코드 및 처리 방법
9. [API 사용 예제](api_examples.md) - 주요 기능 사용 예제

## 시작하기

### 기본 URL

```
http://localhost:8000/api
```

### API 버전

현재 API 버전은 0.1.0입니다.

### 인증

API는 OAuth2 기반의 Bearer 토큰 인증을 사용합니다. 대부분의 엔드포인트는 인증이 필요합니다.

```
Authorization: Bearer {token}
```

토큰은 `/api/auth/login` 엔드포인트를 통해 획득할 수 있습니다.

### 요청 형식

요청 본문은 JSON 형식으로 전송해야 합니다.

```
Content-Type: application/json
```

### 응답 형식

모든 응답은 JSON 형식으로 반환됩니다.

```
Content-Type: application/json
```

## API 문서 접근

API 문서는 다음 URL을 통해 접근할 수 있습니다:

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI 스펙: `/api/openapi.json`

## 지원 및 문의

API 사용 중 문제가 발생하거나 추가 지원이 필요한 경우, 관리자에게 문의하세요.