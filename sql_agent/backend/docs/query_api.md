# 쿼리 API

쿼리 API는 자연어 질의 처리, SQL 쿼리 실행, 쿼리 상태 모니터링 등의 기능을 제공합니다.

## 엔드포인트

### 자연어 질의 처리

```
POST /api/query/natural
```

자연어 질의를 SQL로 변환합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "query": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
  "db_id": "string",
  "use_rag": false,
  "context": "string"
}
```

- `query`: 자연어 질의 문자열
- `db_id`: 데이터베이스 ID (선택적, 지정하지 않으면 현재 연결된 DB)
- `use_rag`: RAG 시스템 사용 여부 (선택적, 기본값: false)
- `context`: 추가 컨텍스트 정보 (선택적)

#### 응답

**성공 (200 OK)**

```json
{
  "query_id": "string",
  "natural_language": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
  "generated_sql": "SELECT TOP 5 p.ProductName, SUM(od.Quantity) AS TotalSales FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE o.OrderDate >= DATEADD(month, -1, GETDATE()) AND o.OrderDate < GETDATE() GROUP BY p.ProductName ORDER BY TotalSales DESC",
  "db_type": "mssql",
  "tables_used": ["Products", "OrderDetails", "Orders"],
  "alternative_queries": [
    {
      "sql": "string",
      "explanation": "string"
    }
  ],
  "explanation": "이 쿼리는 지난 한 달 동안의 주문 데이터에서 제품별 판매량을 계산하고, 판매량이 가장 높은 5개 제품을 반환합니다."
}
```

**실패 (400 Bad Request)**

```json
{
  "detail": "자연어 질의 처리 실패",
  "error_code": "NL_QUERY_ERROR",
  "error_details": "질의가 모호하거나 필요한 정보가 부족합니다."
}
```

### SQL 쿼리 실행

```
POST /api/query/execute
```

SQL 쿼리를 실행합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "query_id": "string",
  "sql": "string",
  "db_id": "string",
  "timeout": 30
}
```

- `query_id`: 쿼리 ID (자연어 질의 처리 응답에서 받은 ID)
- `sql`: 실행할 SQL 쿼리 문자열
- `db_id`: 데이터베이스 ID (선택적, 지정하지 않으면 현재 연결된 DB)
- `timeout`: 쿼리 실행 타임아웃(초) (선택적, 기본값: 30)

#### 응답

**성공 (200 OK)**

```json
{
  "query_id": "string",
  "result_id": "string",
  "status": "completed",
  "execution_time": 1.25,
  "row_count": 5,
  "truncated": false,
  "columns": [
    {
      "name": "ProductName",
      "type": "string"
    },
    {
      "name": "TotalSales",
      "type": "number"
    }
  ],
  "rows": [
    ["Product A", 120],
    ["Product B", 95],
    ["Product C", 87],
    ["Product D", 65],
    ["Product E", 42]
  ]
}
```

**실패 (400 Bad Request)**

```json
{
  "detail": "SQL 쿼리 실행 실패",
  "error_code": "SQL_EXECUTION_ERROR",
  "error_details": "문법 오류 또는 존재하지 않는 테이블/필드 참조",
  "error_position": 25
}
```

### 쿼리 상태 확인

```
GET /api/query/status/{query_id}
```

실행 중인 쿼리의 상태를 확인합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `query_id`: 쿼리 ID

#### 응답

**성공 (200 OK)**

```json
{
  "query_id": "string",
  "status": "executing",
  "progress": 75,
  "elapsed_time": 15.5,
  "estimated_remaining_time": 5.2
}
```

### 쿼리 취소

```
POST /api/query/cancel/{query_id}
```

실행 중인 쿼리를 취소합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `query_id`: 쿼리 ID

#### 응답

**성공 (200 OK)**

```json
{
  "query_id": "string",
  "status": "cancelled",
  "message": "쿼리가 성공적으로 취소되었습니다."
}
```

## 사용 예제

### 자연어 질의 처리

```python
import requests

url = "http://localhost:8000/api/query/natural"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "query": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
    "db_id": "mssql-prod-01"
}

response = requests.post(url, headers=headers, json=data)
query_result = response.json()
query_id = query_result["query_id"]
generated_sql = query_result["generated_sql"]
```

### SQL 쿼리 실행

```python
import requests

url = "http://localhost:8000/api/query/execute"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "query_id": query_id,
    "sql": generated_sql,
    "db_id": "mssql-prod-01",
    "timeout": 60
}

response = requests.post(url, headers=headers, json=data)
execution_result = response.json()
```

### 쿼리 상태 확인

```python
import requests
import time

url = f"http://localhost:8000/api/query/status/{query_id}"
headers = {
    "Authorization": f"Bearer {access_token}"
}

# 쿼리 완료될 때까지 상태 확인
while True:
    response = requests.get(url, headers=headers)
    status_data = response.json()
    
    if status_data["status"] in ["completed", "failed", "cancelled"]:
        break
        
    print(f"Progress: {status_data['progress']}%")
    time.sleep(1)
```