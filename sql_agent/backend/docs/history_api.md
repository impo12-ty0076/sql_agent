# 이력 및 공유 API

이력 및 공유 API는 쿼리 이력 관리, 즐겨찾기, 태그 관리, 쿼리 및 결과 공유 등의 기능을 제공합니다.

## 엔드포인트

### 쿼리 이력 조회

```
GET /api/history
```

사용자의 쿼리 이력을 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 쿼리 파라미터

- `page`: 페이지 번호 (선택적, 기본값: 1)
- `page_size`: 페이지 크기 (선택적, 기본값: 20)
- `sort_by`: 정렬 기준 (선택적, 기본값: "created_at", 옵션: "created_at", "db_name", "query_type")
- `sort_order`: 정렬 순서 (선택적, 기본값: "desc", 옵션: "asc", "desc")
- `filter_db`: 데이터베이스 ID로 필터링 (선택적)
- `filter_tag`: 태그로 필터링 (선택적)
- `filter_favorite`: 즐겨찾기로 필터링 (선택적, 기본값: false)
- `search`: 검색어 (선택적)

#### 응답

**성공 (200 OK)**

```json
{
  "history": [
    {
      "id": "string",
      "query_id": "string",
      "natural_language": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
      "generated_sql": "SELECT TOP 5 p.ProductName, SUM(od.Quantity) AS TotalSales FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE o.OrderDate >= DATEADD(month, -1, GETDATE()) AND o.OrderDate < GETDATE() GROUP BY p.ProductName ORDER BY TotalSales DESC",
      "db_name": "Sales",
      "db_type": "mssql",
      "execution_time": 1.25,
      "row_count": 5,
      "status": "completed",
      "favorite": true,
      "tags": ["sales", "monthly-report"],
      "notes": "월간 판매 보고서용 쿼리",
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total_count": 42,
  "page": 1,
  "total_pages": 3
}
```

### 쿼리 이력 상세 조회

```
GET /api/history/{history_id}
```

특정 쿼리 이력의 상세 정보를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `history_id`: 이력 ID

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "query_id": "string",
  "result_id": "string",
  "natural_language": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
  "generated_sql": "SELECT TOP 5 p.ProductName, SUM(od.Quantity) AS TotalSales FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE o.OrderDate >= DATEADD(month, -1, GETDATE()) AND o.OrderDate < GETDATE() GROUP BY p.ProductName ORDER BY TotalSales DESC",
  "executed_sql": "SELECT TOP 5 p.ProductName, SUM(od.Quantity) AS TotalSales FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE o.OrderDate >= DATEADD(month, -1, GETDATE()) AND o.OrderDate < GETDATE() GROUP BY p.ProductName ORDER BY TotalSales DESC",
  "db_id": "string",
  "db_name": "Sales",
  "db_type": "mssql",
  "execution_time": 1.25,
  "row_count": 5,
  "status": "completed",
  "favorite": true,
  "tags": ["sales", "monthly-report"],
  "notes": "월간 판매 보고서용 쿼리",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-02T00:00:00Z",
  "report_id": "string"
}
```

### 쿼리 이력 즐겨찾기 설정/해제

```
PUT /api/history/{history_id}/favorite
```

쿼리 이력을 즐겨찾기로 설정하거나 해제합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `history_id`: 이력 ID

#### 요청 본문

```json
{
  "favorite": true
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "favorite": true,
  "message": "즐겨찾기 설정이 업데이트되었습니다."
}
```

### 쿼리 이력 태그 관리

```
PUT /api/history/{history_id}/tags
```

쿼리 이력의 태그를 관리합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `history_id`: 이력 ID

#### 요청 본문

```json
{
  "tags": ["sales", "monthly-report", "product-analysis"]
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "tags": ["sales", "monthly-report", "product-analysis"],
  "message": "태그가 업데이트되었습니다."
}
```

### 쿼리 이력 노트 업데이트

```
PUT /api/history/{history_id}/notes
```

쿼리 이력의 노트를 업데이트합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `history_id`: 이력 ID

#### 요청 본문

```json
{
  "notes": "월간 판매 보고서용 쿼리 - 경영진 회의 자료로 사용"
}
```

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "notes": "월간 판매 보고서용 쿼리 - 경영진 회의 자료로 사용",
  "message": "노트가 업데이트되었습니다."
}
```

### 쿼리 재실행

```
POST /api/history/{history_id}/rerun
```

이전에 실행한 쿼리를 재실행합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `history_id`: 이력 ID

#### 요청 본문

```json
{
  "use_original_sql": true,
  "db_id": "string"
}
```

- `use_original_sql`: 원본 SQL 사용 여부 (선택적, 기본값: true)
- `db_id`: 데이터베이스 ID (선택적, 지정하지 않으면 원래 사용한 DB)

#### 응답

**성공 (200 OK)**

```json
{
  "query_id": "string",
  "result_id": "string",
  "status": "executing",
  "message": "쿼리가 재실행되었습니다."
}
```

### 쿼리 공유 링크 생성

```
POST /api/share
```

쿼리 및 결과에 대한 공유 링크를 생성합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 요청 본문

```json
{
  "history_id": "string",
  "expires_in": 7,
  "allowed_users": ["user1@example.com", "user2@example.com"],
  "include_result": true,
  "include_report": true
}
```

- `history_id`: 이력 ID
- `expires_in`: 만료 기간(일) (선택적, 기본값: 7)
- `allowed_users`: 접근 허용 사용자 이메일 목록 (선택적)
- `include_result`: 결과 포함 여부 (선택적, 기본값: true)
- `include_report`: 리포트 포함 여부 (선택적, 기본값: false)

#### 응답

**성공 (200 OK)**

```json
{
  "share_id": "string",
  "access_token": "string",
  "share_url": "http://localhost:8000/shared/abcdef123456",
  "expires_at": "2023-01-08T00:00:00Z",
  "allowed_users": ["user1@example.com", "user2@example.com"]
}
```

### 공유 링크 관리

```
GET /api/share
```

사용자가 생성한 공유 링크 목록을 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "shares": [
    {
      "share_id": "string",
      "history_id": "string",
      "natural_language": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
      "share_url": "http://localhost:8000/shared/abcdef123456",
      "created_at": "2023-01-01T00:00:00Z",
      "expires_at": "2023-01-08T00:00:00Z",
      "access_count": 5
    }
  ]
}
```

### 공유 링크 삭제

```
DELETE /api/share/{share_id}
```

공유 링크를 삭제합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `share_id`: 공유 ID

#### 응답

**성공 (200 OK)**

```json
{
  "message": "공유 링크가 삭제되었습니다."
}
```

### 공유된 쿼리 조회

```
GET /api/shared/{access_token}
```

공유된 쿼리 및 결과를 조회합니다.

#### 경로 파라미터

- `access_token`: 접근 토큰

#### 응답

**성공 (200 OK)**

```json
{
  "history_id": "string",
  "natural_language": "지난 달 판매량이 가장 높은 상위 5개 제품은?",
  "generated_sql": "SELECT TOP 5 p.ProductName, SUM(od.Quantity) AS TotalSales FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE o.OrderDate >= DATEADD(month, -1, GETDATE()) AND o.OrderDate < GETDATE() GROUP BY p.ProductName ORDER BY TotalSales DESC",
  "db_name": "Sales",
  "db_type": "mssql",
  "execution_time": 1.25,
  "created_at": "2023-01-01T00:00:00Z",
  "shared_by": "user@example.com",
  "result": {
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
    ],
    "row_count": 5
  },
  "report": {
    "report_id": "string",
    "title": "지난 달 상위 판매 제품 분석",
    "summary": "이 리포트는 지난 달 판매량이 가장 높은 상위 5개 제품에 대한 분석 결과입니다.",
    "visualizations": [
      {
        "type": "bar",
        "title": "제품별 판매량",
        "image_data": "base64_encoded_image_data"
      }
    ]
  }
}
```

## 사용 예제

### 쿼리 이력 조회

```python
import requests

url = "http://localhost:8000/api/history"
headers = {
    "Authorization": f"Bearer {access_token}"
}
params = {
    "page": 1,
    "page_size": 10,
    "sort_by": "created_at",
    "sort_order": "desc",
    "filter_favorite": True
}

response = requests.get(url, headers=headers, params=params)
history_data = response.json()
```

### 쿼리 즐겨찾기 설정

```python
import requests

history_id = "history_123456"
url = f"http://localhost:8000/api/history/{history_id}/favorite"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "favorite": True
}

response = requests.put(url, headers=headers, json=data)
```

### 쿼리 공유 링크 생성

```python
import requests

url = "http://localhost:8000/api/share"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "history_id": "history_123456",
    "expires_in": 14,
    "allowed_users": ["colleague@example.com"],
    "include_result": True,
    "include_report": True
}

response = requests.post(url, headers=headers, json=data)
share_data = response.json()
share_url = share_data["share_url"]

print(f"공유 URL: {share_url}")
```