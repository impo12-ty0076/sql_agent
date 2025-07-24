# 데이터베이스 API

데이터베이스 API는 데이터베이스 목록 조회, 연결, 스키마 정보 조회 등의 기능을 제공합니다.

## 엔드포인트

### 데이터베이스 목록 조회

```
GET /api/db/list
```

사용자가 접근 권한을 가진 데이터베이스 목록을 반환합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "databases": [
    {
      "id": "string",
      "name": "string",
      "type": "mssql",
      "host": "string",
      "port": 1433,
      "default_schema": "string",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

### 데이터베이스 연결

```
POST /api/db/connect
```

지정된 데이터베이스에 연결합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "db_id": "string"
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "status": "connected",
  "db_id": "string",
  "db_name": "string",
  "db_type": "mssql",
  "connection_id": "string"
}
```

**실패 (400 Bad Request)**

```json
{
  "detail": "데이터베이스 연결 실패",
  "error_code": "DB_CONNECTION_ERROR",
  "error_details": "연결 시간 초과 또는 인증 실패"
}
```

### 데이터베이스 스키마 조회

```
GET /api/db/schema
```

현재 연결된 데이터베이스의 스키마 정보를 반환합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 쿼리 파라미터

- `db_id`: 데이터베이스 ID (선택적, 지정하지 않으면 현재 연결된 DB)

#### 응답

**성공 (200 OK)**

```json
{
  "db_id": "string",
  "schemas": [
    {
      "name": "string",
      "tables": [
        {
          "name": "string",
          "columns": [
            {
              "name": "string",
              "type": "string",
              "nullable": true,
              "default_value": "string",
              "description": "string"
            }
          ],
          "primary_key": ["string"],
          "foreign_keys": [
            {
              "columns": ["string"],
              "reference_table": "string",
              "reference_columns": ["string"]
            }
          ],
          "description": "string"
        }
      ]
    }
  ],
  "last_updated": "2023-01-01T00:00:00Z"
}
```

### 데이터베이스 연결 해제

```
POST /api/db/disconnect
```

현재 연결된 데이터베이스 연결을 해제합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "connection_id": "string"
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "status": "disconnected",
  "connection_id": "string"
}
```

## 사용 예제

### 데이터베이스 목록 조회

```python
import requests

url = "http://localhost:8000/api/db/list"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)
databases = response.json()["databases"]
```

### 데이터베이스 연결

```python
import requests

url = "http://localhost:8000/api/db/connect"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "db_id": "mssql-prod-01"
}

response = requests.post(url, headers=headers, json=data)
connection = response.json()
```

### 데이터베이스 스키마 조회

```python
import requests

url = "http://localhost:8000/api/db/schema"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)
schema = response.json()
```
