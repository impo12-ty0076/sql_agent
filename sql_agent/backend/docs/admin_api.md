# 관리자 API

관리자 API는 사용자 관리, 정책 설정, 시스템 모니터링, 로그 조회 등의 관리자 기능을 제공합니다.

## 엔드포인트

### 사용자 목록 조회

```
GET /api/admin/users
```

시스템에 등록된 사용자 목록을 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 쿼리 파라미터

- `page`: 페이지 번호 (선택적, 기본값: 1)
- `page_size`: 페이지 크기 (선택적, 기본값: 20)
- `sort_by`: 정렬 기준 (선택적, 기본값: "username", 옵션: "username", "email", "role", "last_login")
- `sort_order`: 정렬 순서 (선택적, 기본값: "asc", 옵션: "asc", "desc")
- `search`: 검색어 (선택적)

#### 응답

**성공 (200 OK)**

```json
{
  "users": [
    {
      "id": "string",
      "username": "user1",
      "email": "user1@example.com",
      "role": "user",
      "last_login": "2023-01-01T00:00:00Z",
      "created_at": "2022-01-01T00:00:00Z",
      "status": "active"
    }
  ],
  "total_count": 42,
  "page": 1,
  "total_pages": 3
}
```

### 사용자 상세 정보 조회

```
GET /api/admin/users/{user_id}
```

특정 사용자의 상세 정보를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `user_id`: 사용자 ID

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "username": "user1",
  "email": "user1@example.com",
  "role": "user",
  "last_login": "2023-01-01T00:00:00Z",
  "created_at": "2022-01-01T00:00:00Z",
  "updated_at": "2022-12-01T00:00:00Z",
  "status": "active",
  "preferences": {
    "default_db": "string",
    "theme": "light",
    "results_per_page": 10
  },
  "permissions": {
    "allowed_databases": [
      {
        "db_id": "string",
        "db_type": "mssql",
        "allowed_schemas": ["dbo", "sales"],
        "allowed_tables": ["Products", "Orders"]
      }
    ]
  },
  "usage_statistics": {
    "total_queries": 156,
    "total_execution_time": 325.5,
    "average_execution_time": 2.1,
    "queries_last_30_days": 42,
    "last_active": "2023-01-01T00:00:00Z"
  }
}
```

### 사용자 생성

```
POST /api/admin/users
```

새로운 사용자를 생성합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword",
  "role": "user",
  "permissions": {
    "allowed_databases": [
      {
        "db_id": "string",
        "allowed_schemas": ["dbo", "sales"],
        "allowed_tables": ["Products", "Orders"]
      }
    ]
  }
}
```

#### 응답

**성공 (201 Created)**

```json
{
  "id": "string",
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "user",
  "created_at": "2023-01-01T00:00:00Z",
  "status": "active",
  "message": "사용자가 성공적으로 생성되었습니다."
}
```

### 사용자 업데이트

```
PUT /api/admin/users/{user_id}
```

사용자 정보를 업데이트합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `user_id`: 사용자 ID

#### 요청 본문

```json
{
  "email": "updated@example.com",
  "role": "admin",
  "status": "active",
  "permissions": {
    "allowed_databases": [
      {
        "db_id": "string",
        "allowed_schemas": ["dbo", "sales", "marketing"],
        "allowed_tables": ["Products", "Orders", "Customers"]
      }
    ]
  }
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "username": "user1",
  "email": "updated@example.com",
  "role": "admin",
  "status": "active",
  "message": "사용자 정보가 업데이트되었습니다."
}
```

### 사용자 비밀번호 재설정

```
POST /api/admin/users/{user_id}/reset-password
```

사용자의 비밀번호를 재설정합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `user_id`: 사용자 ID

#### 요청 본문

```json
{
  "new_password": "newsecurepassword",
  "send_email": true
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "message": "비밀번호가 재설정되었습니다."
}
```

### 사용자 비활성화/활성화

```
PUT /api/admin/users/{user_id}/status
```

사용자 계정을 비활성화하거나 활성화합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `user_id`: 사용자 ID

#### 요청 본문

```json
{
  "status": "inactive",
  "reason": "퇴사"
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "username": "user1",
  "status": "inactive",
  "message": "사용자 상태가 변경되었습니다."
}
```

### 정책 목록 조회

```
GET /api/admin/policies
```

시스템 정책 목록을 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "policies": [
    {
      "id": "string",
      "name": "기본 정책",
      "description": "일반 사용자에게 적용되는 기본 정책",
      "settings": {
        "max_queries_per_day": 100,
        "max_query_execution_time": 60,
        "max_result_size": 10000,
        "allowed_query_types": ["SELECT"],
        "blocked_keywords": ["DROP", "DELETE", "UPDATE", "INSERT"]
      },
      "created_at": "2022-01-01T00:00:00Z",
      "updated_at": "2022-01-01T00:00:00Z"
    }
  ]
}
```

### 정책 생성/업데이트

```
PUT /api/admin/policies/{policy_id}
```

시스템 정책을 생성하거나 업데이트합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `policy_id`: 정책 ID

#### 요청 본문

```json
{
  "name": "고급 사용자 정책",
  "description": "데이터 분석가에게 적용되는 고급 정책",
  "settings": {
    "max_queries_per_day": 500,
    "max_query_execution_time": 300,
    "max_result_size": 100000,
    "allowed_query_types": ["SELECT"],
    "blocked_keywords": ["DROP", "DELETE", "UPDATE", "INSERT"]
  }
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "name": "고급 사용자 정책",
  "message": "정책이 업데이트되었습니다."
}
```

### 사용 통계 조회

```
GET /api/admin/statistics
```

시스템 사용 통계를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 쿼리 파라미터

- `period`: 기간 (선택적, 기본값: "last_30_days", 옵션: "today", "last_7_days", "last_30_days", "last_90_days")
- `group_by`: 그룹화 기준 (선택적, 기본값: "day", 옵션: "hour", "day", "week", "month")

#### 응답

**성공 (200 OK)**

```json
{
  "period": "last_30_days",
  "total_queries": 1256,
  "total_users": 42,
  "active_users": 28,
  "average_query_time": 2.5,
  "total_execution_time": 3140.0,
  "query_success_rate": 98.5,
  "top_users": [
    {
      "user_id": "string",
      "username": "user1",
      "query_count": 156
    }
  ],
  "top_databases": [
    {
      "db_id": "string",
      "db_name": "Sales",
      "query_count": 523
    }
  ],
  "query_count_by_time": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "count": 42
    }
  ],
  "error_rate_by_time": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "rate": 1.2
    }
  ]
}
```

### 로그 조회

```
GET /api/admin/logs
```

시스템 로그를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 쿼리 파라미터

- `page`: 페이지 번호 (선택적, 기본값: 1)
- `page_size`: 페이지 크기 (선택적, 기본값: 100)
- `level`: 로그 레벨 (선택적, 옵션: "info", "warning", "error", "critical")
- `category`: 로그 카테고리 (선택적, 옵션: "auth", "query", "system", "security")
- `start_date`: 시작 날짜 (선택적, ISO 8601 형식)
- `end_date`: 종료 날짜 (선택적, ISO 8601 형식)
- `user_id`: 사용자 ID (선택적)
- `search`: 검색어 (선택적)

#### 응답

**성공 (200 OK)**

```json
{
  "logs": [
    {
      "id": "string",
      "timestamp": "2023-01-01T00:00:00Z",
      "level": "error",
      "category": "query",
      "message": "쿼리 실행 중 오류 발생: 테이블 'Products'가 존재하지 않습니다.",
      "user_id": "string",
      "username": "user1",
      "details": {
        "query_id": "string",
        "sql": "SELECT * FROM Products",
        "error_code": "DB_TABLE_NOT_FOUND"
      }
    }
  ],
  "total_count": 1256,
  "page": 1,
  "total_pages": 13
}
```

### 시스템 설정 조회

```
GET /api/admin/system/settings
```

시스템 설정을 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "settings": {
    "general": {
      "system_name": "SQL DB LLM Agent",
      "maintenance_mode": false,
      "default_language": "ko"
    },
    "security": {
      "session_timeout": 3600,
      "password_policy": {
        "min_length": 8,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_number": true,
        "require_special": true
      },
      "mfa_enabled": true
    },
    "query": {
      "default_timeout": 30,
      "max_rows_return": 10000,
      "auto_save_history": true
    },
    "llm": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.1,
      "max_tokens": 2000
    }
  }
}
```

### 시스템 설정 업데이트

```
PUT /api/admin/system/settings
```

시스템 설정을 업데이트합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "settings": {
    "general": {
      "system_name": "SQL DB LLM Agent Pro",
      "maintenance_mode": false
    },
    "security": {
      "session_timeout": 1800
    },
    "query": {
      "default_timeout": 60
    },
    "llm": {
      "provider": "azure-openai",
      "model": "gpt-4-turbo",
      "temperature": 0.2
    }
  }
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "message": "시스템 설정이 업데이트되었습니다."
}
```

### 데이터베이스 연결 관리

```
GET /api/admin/system/databases
```

시스템에 등록된 데이터베이스 연결 정보를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "databases": [
    {
      "id": "string",
      "name": "Sales",
      "type": "mssql",
      "host": "db-server.example.com",
      "port": 1433,
      "default_schema": "dbo",
      "created_at": "2022-01-01T00:00:00Z",
      "updated_at": "2022-01-01T00:00:00Z",
      "status": "active"
    }
  ]
}
```

### 데이터베이스 연결 추가/업데이트

```
PUT /api/admin/system/databases/{db_id}
```

데이터베이스 연결 정보를 추가하거나 업데이트합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `db_id`: 데이터베이스 ID

#### 요청 본문

```json
{
  "name": "Marketing",
  "type": "mssql",
  "host": "db-server.example.com",
  "port": 1433,
  "default_schema": "dbo",
  "connection_config": {
    "username": "dbuser",
    "password": "dbpassword",
    "options": {
      "encrypt": true,
      "trustServerCertificate": false
    }
  }
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "name": "Marketing",
  "type": "mssql",
  "message": "데이터베이스 연결 정보가 업데이트되었습니다."
}
```

### 시스템 백업 생성

```
POST /api/admin/system/backup
```

시스템 설정 및 데이터 백업을 생성합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "include_user_data": true,
  "include_query_history": true,
  "include_system_settings": true
}
```

#### 응답

**성공 (202 Accepted)**

```json
{
  "backup_id": "string",
  "status": "processing",
  "estimated_completion_time": "2023-01-01T00:05:00Z"
}
```

### 시스템 백업 복원

```
POST /api/admin/system/restore
```

백업에서 시스템을 복원합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "backup_id": "string",
  "restore_user_data": true,
  "restore_query_history": true,
  "restore_system_settings": true
}
```

#### 응답

**성공 (202 Accepted)**

```json
{
  "restore_id": "string",
  "status": "processing",
  "estimated_completion_time": "2023-01-01T00:10:00Z"
}
```

## 사용 예제

### 사용자 목록 조회

```python
import requests

url = "http://localhost:8000/api/admin/users"
headers = {
    "Authorization": f"Bearer {access_token}"
}
params = {
    "page": 1,
    "page_size": 20,
    "sort_by": "last_login",
    "sort_order": "desc"
}

response = requests.get(url, headers=headers, params=params)
users_data = response.json()
```

### 정책 업데이트

```python
import requests

policy_id = "policy_default"
url = f"http://localhost:8000/api/admin/policies/{policy_id}"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
  "name": "기본 정책",
  "description": "일반 사용자에게 적용되는 기본 정책",
  "settings": {
    "max_queries_per_day": 200,
    "max_query_execution_time": 120,
    "max_result_size": 20000,
    "allowed_query_types": ["SELECT"],
    "blocked_keywords": ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]
  }
}

response = requests.put(url, headers=headers, json=data)
```

### 시스템 사용 통계 조회

```python
import requests

url = "http://localhost:8000/api/admin/statistics"
headers = {
    "Authorization": f"Bearer {access_token}"
}
params = {
    "period": "last_30_days",
    "group_by": "day"
}

response = requests.get(url, headers=headers, params=params)
stats_data = response.json()
```
