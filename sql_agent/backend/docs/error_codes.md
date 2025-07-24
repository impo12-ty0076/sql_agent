# 오류 코드 및 처리 방법

SQL DB LLM Agent API는 구조화된 오류 응답을 제공하여 클라이언트가 오류를 효과적으로 처리할 수 있도록 합니다. 이 문서는 API에서 발생할 수 있는 오류 코드와 그 처리 방법에 대해 설명합니다.

## 오류 응답 형식

모든 오류 응답은 다음과 같은 일관된 형식을 따릅니다:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "사용자 친화적인 오류 메시지",
  "details": {
    // 오류 관련 추가 정보 (선택적)
  },
  "suggestions": ["오류 해결을 위한 제안 사항"],
  "retryable": false
}
```

- `status`: 항상 "error"로 설정됩니다.
- `code`: 오류 유형을 식별하는 고유 코드입니다.
- `message`: 사용자 친화적인 오류 설명입니다.
- `details`: 오류에 대한 추가 정보를 포함하는 객체입니다 (선택적).
- `suggestions`: 오류 해결을 위한 제안 사항 목록입니다 (선택적).
- `retryable`: 동일한 요청을 재시도하여 오류를 해결할 수 있는지 여부를 나타냅니다.

## HTTP 상태 코드

API는 다음과 같은 HTTP 상태 코드를 사용합니다:

- `400 Bad Request`: 클라이언트 요청에 오류가 있습니다.
- `401 Unauthorized`: 인증이 필요하거나 제공된 인증 정보가 유효하지 않습니다.
- `403 Forbidden`: 인증은 성공했지만 요청된 리소스에 접근할 권한이 없습니다.
- `404 Not Found`: 요청된 리소스를 찾을 수 없습니다.
- `409 Conflict`: 요청이 현재 서버 상태와 충돌합니다.
- `422 Unprocessable Entity`: 요청은 유효하지만 처리할 수 없습니다.
- `429 Too Many Requests`: 요청 횟수 제한을 초과했습니다.
- `500 Internal Server Error`: 서버 내부 오류가 발생했습니다.
- `503 Service Unavailable`: 서비스를 일시적으로 사용할 수 없습니다.

## 오류 코드 목록

### 인증 및 권한 오류

| 코드                       | HTTP 상태 | 설명                             | 처리 방법                                                   |
| -------------------------- | --------- | -------------------------------- | ----------------------------------------------------------- |
| `AUTH_INVALID_CREDENTIALS` | 401       | 잘못된 사용자 이름 또는 비밀번호 | 사용자 인증 정보를 확인하고 다시 시도하세요.                |
| `AUTH_EXPIRED_TOKEN`       | 401       | 만료된 액세스 토큰               | 토큰을 갱신하거나 다시 로그인하세요.                        |
| `AUTH_INVALID_TOKEN`       | 401       | 유효하지 않은 액세스 토큰        | 다시 로그인하여 새 토큰을 발급받으세요.                     |
| `AUTH_MISSING_TOKEN`       | 401       | 액세스 토큰이 제공되지 않음      | Authorization 헤더에 Bearer 토큰을 포함하세요.              |
| `AUTH_ACCOUNT_LOCKED`      | 401       | 계정이 잠겨 있음                 | 관리자에게 문의하여 계정 잠금을 해제하세요.                 |
| `AUTH_PERMISSION_DENIED`   | 403       | 요청된 작업에 대한 권한 없음     | 필요한 권한을 요청하거나 권한이 있는 계정으로 로그인하세요. |

### 데이터베이스 연결 오류

| 코드                  | HTTP 상태 | 설명                               | 처리 방법                                         |
| --------------------- | --------- | ---------------------------------- | ------------------------------------------------- |
| `DB_CONNECTION_ERROR` | 400       | 데이터베이스 연결 실패             | 데이터베이스 서버 상태와 연결 정보를 확인하세요.  |
| `DB_AUTH_ERROR`       | 400       | 데이터베이스 인증 실패             | 데이터베이스 사용자 이름과 비밀번호를 확인하세요. |
| `DB_TIMEOUT`          | 408       | 데이터베이스 연결 시간 초과        | 네트워크 상태를 확인하고 다시 시도하세요.         |
| `DB_NOT_FOUND`        | 404       | 지정된 데이터베이스를 찾을 수 없음 | 데이터베이스 ID를 확인하고 다시 시도하세요.       |
| `DB_ACCESS_DENIED`    | 403       | 데이터베이스 접근 권한 없음        | 데이터베이스 접근 권한을 요청하세요.              |
| `DB_SCHEMA_ERROR`     | 400       | 데이터베이스 스키마 조회 실패      | 데이터베이스 구조와 권한을 확인하세요.            |

### 쿼리 오류

| 코드                    | HTTP 상태 | 설명                          | 처리 방법                                                     |
| ----------------------- | --------- | ----------------------------- | ------------------------------------------------------------- |
| `QUERY_SYNTAX_ERROR`    | 400       | SQL 구문 오류                 | SQL 쿼리의 구문을 확인하고 수정하세요.                        |
| `QUERY_EXECUTION_ERROR` | 400       | SQL 쿼리 실행 실패            | 오류 세부 정보를 확인하고 쿼리를 수정하세요.                  |
| `QUERY_TIMEOUT`         | 408       | 쿼리 실행 시간 초과           | 쿼리를 최적화하거나 타임아웃 값을 늘리세요.                   |
| `QUERY_CANCELLED`       | 400       | 사용자에 의해 쿼리 취소됨     | 정보용 메시지로, 추가 조치가 필요하지 않습니다.               |
| `QUERY_LIMIT_EXCEEDED`  | 400       | 쿼리 결과 크기 제한 초과      | 쿼리를 더 구체적으로 작성하거나 LIMIT/TOP 절을 사용하세요.    |
| `QUERY_NOT_FOUND`       | 404       | 지정된 쿼리 ID를 찾을 수 없음 | 쿼리 ID를 확인하고 다시 시도하세요.                           |
| `QUERY_FORBIDDEN`       | 403       | 금지된 SQL 명령어 사용        | 읽기 전용 쿼리만 허용됩니다. DDL/DML 문은 사용할 수 없습니다. |

### 자연어 처리 오류

| 코드                 | HTTP 상태 | 설명                    | 처리 방법                                              |
| -------------------- | --------- | ----------------------- | ------------------------------------------------------ |
| `NL_QUERY_ERROR`     | 400       | 자연어 질의 처리 실패   | 질의를 더 명확하게 작성하고 다시 시도하세요.           |
| `NL_AMBIGUOUS_QUERY` | 400       | 모호한 자연어 질의      | 질의를 더 구체적으로 작성하고 다시 시도하세요.         |
| `NL_SCHEMA_MISMATCH` | 400       | 질의와 DB 스키마 불일치 | 데이터베이스 스키마에 맞게 질의를 수정하세요.          |
| `NL_CONTEXT_ERROR`   | 400       | 대화 컨텍스트 처리 오류 | 새로운 대화를 시작하거나 질의를 독립적으로 작성하세요. |

### LLM 서비스 오류

| 코드                   | HTTP 상태 | 설명                       | 처리 방법                                      |
| ---------------------- | --------- | -------------------------- | ---------------------------------------------- |
| `LLM_SERVICE_ERROR`    | 503       | LLM 서비스 호출 실패       | 잠시 후 다시 시도하세요.                       |
| `LLM_QUOTA_EXCEEDED`   | 429       | LLM API 할당량 초과        | 잠시 후 다시 시도하거나 관리자에게 문의하세요. |
| `LLM_TIMEOUT`          | 408       | LLM 서비스 응답 시간 초과  | 잠시 후 다시 시도하세요.                       |
| `LLM_INVALID_RESPONSE` | 500       | LLM에서 유효하지 않은 응답 | 질의를 단순화하고 다시 시도하세요.             |

### 결과 및 리포트 오류

| 코드                      | HTTP 상태 | 설명                            | 처리 방법                                  |
| ------------------------- | --------- | ------------------------------- | ------------------------------------------ |
| `RESULT_NOT_FOUND`        | 404       | 지정된 결과 ID를 찾을 수 없음   | 결과 ID를 확인하고 다시 시도하세요.        |
| `RESULT_EXPIRED`          | 410       | 결과가 만료됨                   | 쿼리를 다시 실행하세요.                    |
| `REPORT_GENERATION_ERROR` | 500       | 리포트 생성 실패                | 오류 세부 정보를 확인하고 다시 시도하세요. |
| `REPORT_NOT_FOUND`        | 404       | 지정된 리포트 ID를 찾을 수 없음 | 리포트 ID를 확인하고 다시 시도하세요.      |
| `VISUALIZATION_ERROR`     | 500       | 시각화 생성 실패                | 데이터 형식을 확인하고 다시 시도하세요.    |

### 이력 및 공유 오류

| 코드                  | HTTP 상태 | 설명                          | 처리 방법                               |
| --------------------- | --------- | ----------------------------- | --------------------------------------- |
| `HISTORY_NOT_FOUND`   | 404       | 지정된 이력 ID를 찾을 수 없음 | 이력 ID를 확인하고 다시 시도하세요.     |
| `SHARE_NOT_FOUND`     | 404       | 지정된 공유 ID를 찾을 수 없음 | 공유 ID를 확인하고 다시 시도하세요.     |
| `SHARE_EXPIRED`       | 410       | 공유 링크가 만료됨            | 새로운 공유 링크를 생성하세요.          |
| `SHARE_ACCESS_DENIED` | 403       | 공유 항목에 접근할 권한 없음  | 공유 소유자에게 접근 권한을 요청하세요. |

### 관리자 오류

| 코드                     | HTTP 상태 | 설명                                         | 처리 방법                                  |
| ------------------------ | --------- | -------------------------------------------- | ------------------------------------------ |
| `ADMIN_USER_NOT_FOUND`   | 404       | 지정된 사용자를 찾을 수 없음                 | 사용자 ID를 확인하고 다시 시도하세요.      |
| `ADMIN_USER_EXISTS`      | 409       | 동일한 사용자 이름 또는 이메일이 이미 존재함 | 다른 사용자 이름 또는 이메일을 사용하세요. |
| `ADMIN_POLICY_NOT_FOUND` | 404       | 지정된 정책을 찾을 수 없음                   | 정책 ID를 확인하고 다시 시도하세요.        |
| `ADMIN_BACKUP_ERROR`     | 500       | 백업 생성 실패                               | 오류 세부 정보를 확인하고 다시 시도하세요. |
| `ADMIN_RESTORE_ERROR`    | 500       | 백업 복원 실패                               | 오류 세부 정보를 확인하고 다시 시도하세요. |

### 시스템 오류

| 코드                  | HTTP 상태 | 설명                         | 처리 방법                                   |
| --------------------- | --------- | ---------------------------- | ------------------------------------------- |
| `SYSTEM_MAINTENANCE`  | 503       | 시스템 유지보수 중           | 유지보수가 완료된 후 다시 시도하세요.       |
| `SYSTEM_OVERLOADED`   | 503       | 시스템 과부하                | 잠시 후 다시 시도하세요.                    |
| `SYSTEM_ERROR`        | 500       | 내부 서버 오류               | 관리자에게 문의하세요.                      |
| `RATE_LIMIT_EXCEEDED` | 429       | 요청 횟수 제한 초과          | 요청 빈도를 줄이고 잠시 후 다시 시도하세요. |
| `VALIDATION_ERROR`    | 400       | 요청 데이터 유효성 검사 실패 | 요청 데이터를 확인하고 수정하세요.          |

## 오류 처리 예제

### 클라이언트 측 오류 처리

```python
import requests

def handle_api_error(response):
    """API 오류 응답 처리"""
    try:
        error_data = response.json()
        error_code = error_data.get("code", "UNKNOWN_ERROR")
        error_message = error_data.get("message", "알 수 없는 오류가 발생했습니다.")
        suggestions = error_data.get("suggestions", [])
        retryable = error_data.get("retryable", False)

        print(f"오류 코드: {error_code}")
        print(f"오류 메시지: {error_message}")

        if suggestions:
            print("제안 사항:")
            for suggestion in suggestions:
                print(f"- {suggestion}")

        if retryable:
            print("이 요청은 재시도할 수 있습니다.")

        # 오류 코드별 처리
        if error_code.startswith("AUTH_"):
            # 인증 관련 오류 처리
            if error_code == "AUTH_EXPIRED_TOKEN":
                print("토큰이 만료되었습니다. 다시 로그인합니다.")
                # 토큰 갱신 또는 재로그인 로직
            else:
                print("인증 오류가 발생했습니다. 다시 로그인하세요.")

        elif error_code.startswith("DB_"):
            # 데이터베이스 관련 오류 처리
            print("데이터베이스 오류가 발생했습니다.")

        elif error_code.startswith("QUERY_"):
            # 쿼리 관련 오류 처리
            print("쿼리 오류가 발생했습니다.")

        elif error_code == "RATE_LIMIT_EXCEEDED":
            # 요청 제한 초과 처리
            print("요청 횟수 제한을 초과했습니다. 잠시 후 다시 시도하세요.")
            # 지수 백오프 로직 구현

        elif error_code == "SYSTEM_MAINTENANCE":
            # 시스템 유지보수 처리
            print("시스템이 유지보수 중입니다. 나중에 다시 시도하세요.")

        else:
            # 기타 오류 처리
            print("예상치 못한 오류가 발생했습니다.")

    except ValueError:
        # JSON 파싱 실패
        print(f"오류 응답 파싱 실패: {response.text}")

# API 호출 예제
try:
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": "SELECT * FROM NonExistentTable",
        "db_id": "mssql-prod-01"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code >= 400:
        handle_api_error(response)
    else:
        result = response.json()
        print("쿼리 실행 성공!")

except requests.RequestException as e:
    print(f"요청 실패: {e}")
```

### 특정 오류 코드 처리

```python
import requests
import time

def execute_query_with_retry(sql, db_id, max_retries=3, retry_delay=2):
    """재시도 로직이 포함된 쿼리 실행 함수"""
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": sql,
        "db_id": db_id
    }

    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                return response.json()

            error_data = response.json()
            error_code = error_data.get("code", "UNKNOWN_ERROR")

            # 재시도 가능한 오류인 경우
            if error_data.get("retryable", False) or error_code in [
                "DB_CONNECTION_ERROR",
                "DB_TIMEOUT",
                "QUERY_TIMEOUT",
                "LLM_SERVICE_ERROR",
                "SYSTEM_OVERLOADED"
            ]:
                retries += 1
                wait_time = retry_delay * (2 ** (retries - 1))  # 지수 백오프
                print(f"재시도 가능한 오류 발생: {error_code}. {wait_time}초 후 재시도 ({retries}/{max_retries})...")
                time.sleep(wait_time)
                continue

            # 재시도할 수 없는 오류
            print(f"오류 발생: {error_code} - {error_data.get('message')}")
            return error_data

        except requests.RequestException as e:
            retries += 1
            wait_time = retry_delay * (2 ** (retries - 1))
            print(f"요청 실패: {e}. {wait_time}초 후 재시도 ({retries}/{max_retries})...")
            time.sleep(wait_time)

    return {"status": "error", "code": "MAX_RETRIES_EXCEEDED", "message": "최대 재시도 횟수를 초과했습니다."}

# 사용 예제
result = execute_query_with_retry(
    sql="SELECT TOP 10 * FROM Products",
    db_id="mssql-prod-01"
)

if result.get("status") != "error":
    print("쿼리 실행 성공!")
    # 결과 처리
else:
    print(f"쿼리 실행 실패: {result.get('message')}")
```

## 오류 로깅 및 보고

클라이언트 애플리케이션에서는 API 오류를 적절히 로깅하고 필요한 경우 사용자에게 알리는 것이 좋습니다. 심각한 오류나 예상치 못한 오류가 발생한 경우 관리자에게 보고하여 시스템 개선에 도움이 될 수 있습니다.

```python
import logging
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="api_errors.log"
)
logger = logging.getLogger("api_client")

def log_api_error(response, request_data=None):
    """API 오류 로깅"""
    try:
        error_data = response.json()
        error_code = error_data.get("code", "UNKNOWN_ERROR")
        error_message = error_data.get("message", "알 수 없는 오류가 발생했습니다.")

        log_data = {
            "status_code": response.status_code,
            "error_code": error_code,
            "error_message": error_message,
            "request_url": response.request.url,
            "request_method": response.request.method
        }

        if request_data:
            log_data["request_data"] = request_data

        if error_code.startswith(("SYSTEM_", "LLM_SERVICE_")):
            # 시스템 오류는 ERROR 레벨로 로깅
            logger.error(f"API 시스템 오류: {error_code}", extra=log_data)
        else:
            # 기타 오류는 WARNING 레벨로 로깅
            logger.warning(f"API 오류: {error_code}", extra=log_data)

    except ValueError:
        # JSON 파싱 실패
        logger.error(f"API 응답 파싱 실패: {response.text}", extra={
            "status_code": response.status_code,
            "request_url": response.request.url,
            "request_method": response.request.method
        })

# 사용 예제
try:
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": "SELECT * FROM NonExistentTable",
        "db_id": "mssql-prod-01"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code >= 400:
        log_api_error(response, data)
        # 사용자에게 적절한 오류 메시지 표시
    else:
        result = response.json()
        # 결과 처리

except requests.RequestException as e:
    logger.error(f"API 요청 실패: {e}", extra={
        "url": url,
        "method": "POST"
    })
    # 사용자에게 연결 오류 메시지 표시
```
