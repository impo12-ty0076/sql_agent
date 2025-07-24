# 결과 API

결과 API는 쿼리 결과 조회, 결과 요약 생성, 리포트 생성 등의 기능을 제공합니다.

## 엔드포인트

### 쿼리 결과 조회

```
GET /api/result/{result_id}
```

쿼리 실행 결과를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `result_id`: 결과 ID

#### 쿼리 파라미터

- `page`: 페이지 번호 (선택적, 기본값: 1)
- `page_size`: 페이지 크기 (선택적, 기본값: 100)

#### 응답

**성공 (200 OK)**

```json
{
  "result_id": "string",
  "query_id": "string",
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
  "row_count": 5,
  "total_row_count": 5,
  "page": 1,
  "total_pages": 1,
  "truncated": false,
  "execution_time": 1.25
}
```

### 결과 요약 생성

```
POST /api/result/{result_id}/summary
```

쿼리 결과에 대한 자연어 요약을 생성합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `result_id`: 결과 ID

#### 요청 본문

```json
{
  "detail_level": "medium"
}
```

- `detail_level`: 요약 상세도 (선택적, 기본값: "medium", 옵션: "low", "medium", "high")

#### 응답

**성공 (200 OK)**

```json
{
  "result_id": "string",
  "summary": "지난 달 판매량이 가장 높은 제품은 Product A(120개)이며, 그 뒤를 Product B(95개), Product C(87개), Product D(65개), Product E(42개)가 따르고 있습니다. 상위 5개 제품의 총 판매량은 409개입니다.",
  "insights": [
    "Product A는 2위 제품보다 26% 더 높은 판매량을 기록했습니다.",
    "상위 2개 제품이 전체 판매량의 52%를 차지합니다.",
    "Product E는 상위 5개 제품 중 가장 낮은 판매량을 기록했으며, 1위 제품의 35% 수준입니다."
  ],
  "generated_at": "2023-01-01T00:00:00Z"
}
```

### 리포트 생성 요청

```
POST /api/result/{result_id}/report
```

쿼리 결과를 기반으로 데이터 분석 리포트 생성을 요청합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `result_id`: 결과 ID

#### 요청 본문

```json
{
  "report_type": "comprehensive",
  "visualizations": ["bar", "pie"],
  "include_code": true
}
```

- `report_type`: 리포트 유형 (선택적, 기본값: "standard", 옵션: "basic", "standard", "comprehensive")
- `visualizations`: 포함할 시각화 유형 (선택적, 기본값: 자동 선택)
- `include_code`: 파이썬 코드 포함 여부 (선택적, 기본값: false)

#### 응답

**성공 (202 Accepted)**

```json
{
  "result_id": "string",
  "report_id": "string",
  "status": "processing",
  "estimated_completion_time": "2023-01-01T00:05:00Z"
}
```

### 리포트 상태 확인

```
GET /api/report/{report_id}/status
```

리포트 생성 상태를 확인합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `report_id`: 리포트 ID

#### 응답

**성공 (200 OK)**

```json
{
  "report_id": "string",
  "status": "completed",
  "progress": 100,
  "message": "리포트 생성이 완료되었습니다."
}
```

### 리포트 조회

```
GET /api/report/{report_id}
```

생성된 리포트를 조회합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `report_id`: 리포트 ID

#### 응답

**성공 (200 OK)**

```json
{
  "report_id": "string",
  "result_id": "string",
  "title": "지난 달 상위 판매 제품 분석",
  "summary": "이 리포트는 지난 달 판매량이 가장 높은 상위 5개 제품에 대한 분석 결과입니다.",
  "insights": [
    "Product A는 전체 판매량의 29%를 차지하며 가장 인기 있는 제품입니다.",
    "상위 2개 제품(Product A, Product B)이 전체 판매량의 절반 이상을 차지합니다.",
    "Product E는 상위 5개 제품 중 가장 낮은 판매량을 기록했으며, 개선이 필요합니다."
  ],
  "visualizations": [
    {
      "id": "string",
      "type": "bar",
      "title": "제품별 판매량",
      "description": "지난 달 상위 5개 제품의 판매량 비교",
      "image_data": "base64_encoded_image_data"
    },
    {
      "id": "string",
      "type": "pie",
      "title": "판매량 비율",
      "description": "지난 달 상위 5개 제품의 판매량 비율",
      "image_data": "base64_encoded_image_data"
    }
  ],
  "python_code": "import pandas as pd\nimport matplotlib.pyplot as plt\n\n# 데이터 로드\ndata = {\n    'ProductName': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],\n    'TotalSales': [120, 95, 87, 65, 42]\n}\ndf = pd.DataFrame(data)\n\n# 바 차트 생성\nplt.figure(figsize=(10, 6))\nplt.bar(df['ProductName'], df['TotalSales'])\nplt.title('제품별 판매량')\nplt.xlabel('제품명')\nplt.ylabel('판매량')\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.savefig('bar_chart.png')\n\n# 파이 차트 생성\nplt.figure(figsize=(8, 8))\nplt.pie(df['TotalSales'], labels=df['ProductName'], autopct='%1.1f%%')\nplt.title('판매량 비율')\nplt.axis('equal')\nplt.tight_layout()\nplt.savefig('pie_chart.png')",
  "created_at": "2023-01-01T00:05:00Z"
}
```

### 리포트 다운로드

```
GET /api/report/{report_id}/download
```

생성된 리포트를 PDF 형식으로 다운로드합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 경로 파라미터

- `report_id`: 리포트 ID

#### 쿼리 파라미터

- `format`: 다운로드 형식 (선택적, 기본값: "pdf", 옵션: "pdf", "html", "json")

#### 응답

**성공 (200 OK)**

파일 다운로드 응답 (Content-Type: application/pdf, application/html 또는 application/json)

## 사용 예제

### 쿼리 결과 조회

```python
import requests

url = f"http://localhost:8000/api/result/{result_id}"
headers = {
    "Authorization": f"Bearer {access_token}"
}
params = {
    "page": 1,
    "page_size": 100
}

response = requests.get(url, headers=headers, params=params)
result_data = response.json()
```

### 결과 요약 생성

```python
import requests

url = f"http://localhost:8000/api/result/{result_id}/summary"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "detail_level": "high"
}

response = requests.post(url, headers=headers, json=data)
summary_data = response.json()
```

### 리포트 생성 및 조회

```python
import requests
import time

# 리포트 생성 요청
url = f"http://localhost:8000/api/result/{result_id}/report"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "report_type": "comprehensive",
    "visualizations": ["bar", "pie", "line"],
    "include_code": true
}

response = requests.post(url, headers=headers, json=data)
report_request = response.json()
report_id = report_request["report_id"]

# 리포트 상태 확인
status_url = f"http://localhost:8000/api/report/{report_id}/status"
while True:
    response = requests.get(status_url, headers=headers)
    status_data = response.json()

    if status_data["status"] == "completed":
        break

    print(f"Progress: {status_data['progress']}%")
    time.sleep(2)

# 리포트 조회
report_url = f"http://localhost:8000/api/report/{report_id}"
response = requests.get(report_url, headers=headers)
report_data = response.json()

# 리포트 다운로드
download_url = f"http://localhost:8000/api/report/{report_id}/download"
params = {
    "format": "pdf"
}
response = requests.get(download_url, headers=headers, params=params)

# PDF 파일 저장
with open("report.pdf", "wb") as f:
    f.write(response.content)
```
