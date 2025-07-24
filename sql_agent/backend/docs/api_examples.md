# API 사용 예제

이 문서는 SQL DB LLM Agent API의 주요 기능을 사용하는 방법에 대한 예제 코드를 제공합니다. 모든 예제는 Python을 사용하여 작성되었습니다.

## 목차

1. [인증 및 세션 관리](#1-인증-및-세션-관리)
2. [데이터베이스 연결](#2-데이터베이스-연결)
3. [자연어 질의 처리](#3-자연어-질의-처리)
4. [SQL 쿼리 실행](#4-sql-쿼리-실행)
5. [결과 처리 및 분석](#5-결과-처리-및-분석)
6. [이력 관리 및 공유](#6-이력-관리-및-공유)
7. [오류 처리](#7-오류-처리)
8. [관리자 기능](#8-관리자-기능)

## 1. 인증 및 세션 관리

### 로그인 및 토큰 획득

```python
import requests

def login(username, password):
    """사용자 로그인 및 토큰 획득"""
    url = "http://localhost:8000/api/auth/login"
    data = {
        "username": username,
        "password": password
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"로그인 실패: {response.status_code}")
        try:
            error_data = response.json()
            print(f"오류: {error_data.get('detail', '알 수 없는 오류')}")
        except:
            print(f"응답: {response.text}")
        return None

# 사용 예제
access_token = login("user", "password")
if access_token:
    print(f"로그인 성공! 토큰: {access_token[:10]}...")
```

### 현재 사용자 정보 조회

```python
import requests

def get_current_user(access_token):
    """현재 인증된 사용자 정보 조회"""
    url = "http://localhost:8000/api/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"사용자 정보 조회 실패: {response.status_code}")
        return None

# 사용 예제
user_info = get_current_user(access_token)
if user_info:
    print(f"사용자: {user_info['username']}")
    print(f"이메일: {user_info['email']}")
    print(f"역할: {user_info['role']}")
```

### 로그아웃

````python
import requests

def logout(access_token):
    """사용자 로그아웃"""
    url = "http://localhost:8000/api/auth/logout"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return True
    else:
        print(f"로그아웃 실패: {response.status_code}")
        return False

# 사용 예제
if logout(access_token):
    print("로그아웃 성공!")
```##
2. 데이터베이스 연결

### 데이터베이스 목록 조회

```python
import requests

def get_databases(access_token):
    """사용자가 접근 가능한 데이터베이스 목록 조회"""
    url = "http://localhost:8000/api/db/list"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["databases"]
    else:
        print(f"데이터베이스 목록 조회 실패: {response.status_code}")
        return None

# 사용 예제
databases = get_databases(access_token)
if databases:
    print(f"사용 가능한 데이터베이스: {len(databases)}개")
    for db in databases:
        print(f"- {db['name']} ({db['type']}): {db['host']}:{db['port']}")
````

### 데이터베이스 연결

```python
import requests

def connect_database(access_token, db_id):
    """데이터베이스 연결"""
    url = "http://localhost:8000/api/db/connect"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "db_id": db_id
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"데이터베이스 연결 실패: {response.status_code}")
        try:
            error_data = response.json()
            print(f"오류: {error_data.get('detail', '알 수 없는 오류')}")
        except:
            print(f"응답: {response.text}")
        return None

# 사용 예제
connection = connect_database(access_token, "mssql-prod-01")
if connection:
    print(f"데이터베이스 연결 성공: {connection['db_name']} (연결 ID: {connection['connection_id']})")
```

### 데이터베이스 스키마 조회

````python
import requests

def get_database_schema(access_token, db_id=None):
    """데이터베이스 스키마 정보 조회"""
    url = "http://localhost:8000/api/db/schema"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {}
    if db_id:
        params["db_id"] = db_id

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"스키마 조회 실패: {response.status_code}")
        return None

# 사용 예제
schema = get_database_schema(access_token)
if schema:
    print(f"데이터베이스: {schema['db_id']}")
    print(f"스키마 수: {len(schema['schemas'])}")

    # 테이블 정보 출력
    for s in schema['schemas']:
        print(f"\n스키마: {s['name']}")
        print(f"테이블 수: {len(s['tables'])}")

        for table in s['tables'][:3]:  # 처음 3개 테이블만 출력
            print(f"  - {table['name']} (컬럼 수: {len(table['columns'])})")
            for column in table['columns'][:3]:  # 처음 3개 컬럼만 출력
                print(f"    - {column['name']} ({column['type']})")
```#
# 3. 자연어 질의 처리

### 자연어 질의를 SQL로 변환

```python
import requests

def natural_language_to_sql(access_token, query, db_id=None, use_rag=False):
    """자연어 질의를 SQL로 변환"""
    url = "http://localhost:8000/api/query/natural"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "use_rag": use_rag
    }
    if db_id:
        data["db_id"] = db_id

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"자연어 질의 처리 실패: {response.status_code}")
        try:
            error_data = response.json()
            print(f"오류: {error_data.get('detail', '알 수 없는 오류')}")
        except:
            print(f"응답: {response.text}")
        return None

# 사용 예제
query_result = natural_language_to_sql(
    access_token,
    "지난 달 판매량이 가장 높은 상위 5개 제품은?",
    db_id="mssql-prod-01"
)

if query_result:
    print("자연어 질의:", query_result["natural_language"])
    print("\n생성된 SQL:")
    print(query_result["generated_sql"])
    print("\n설명:", query_result["explanation"])
    print("\n사용된 테이블:", ", ".join(query_result["tables_used"]))
````

### RAG 시스템을 사용한 질의

````python
import requests

def rag_query(access_token, query, db_id=None):
    """RAG 시스템을 사용한 자연어 질의"""
    url = "http://localhost:8000/api/query/natural"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "use_rag": True
    }
    if db_id:
        data["db_id"] = db_id

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"RAG 질의 처리 실패: {response.status_code}")
        return None

# 사용 예제
rag_result = rag_query(
    access_token,
    "판매 데이터의 구조와 주요 테이블을 설명해주세요.",
    db_id="mssql-prod-01"
)

if rag_result:
    print("RAG 응답:")
    print(rag_result["rag_response"])
    print("\n참조 소스:")
    for source in rag_result["sources"]:
        print(f"- {source['title']}: {source['relevance_score']}")
```#
# 4. SQL 쿼리 실행

### SQL 쿼리 실행

```python
import requests

def execute_sql_query(access_token, sql, query_id=None, db_id=None, timeout=30):
    """SQL 쿼리 실행"""
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": sql,
        "timeout": timeout
    }
    if query_id:
        data["query_id"] = query_id
    if db_id:
        data["db_id"] = db_id

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"쿼리 실행 실패: {response.status_code}")
        try:
            error_data = response.json()
            print(f"오류: {error_data.get('detail', '알 수 없는 오류')}")
            if "error_details" in error_data:
                print(f"상세 오류: {error_data['error_details']}")
        except:
            print(f"응답: {response.text}")
        return None

# 사용 예제 - 자연어 질의 결과로 얻은 SQL 실행
if query_result:
    sql = query_result["generated_sql"]
    query_id = query_result["query_id"]

    execution_result = execute_sql_query(
        access_token,
        sql,
        query_id=query_id,
        timeout=60
    )

    if execution_result:
        print(f"쿼리 실행 완료 (실행 시간: {execution_result['execution_time']}초)")
        print(f"결과 행 수: {execution_result['row_count']}")

        # 결과 컬럼 출력
        print("\n컬럼:")
        for col in execution_result['columns']:
            print(f"- {col['name']} ({col['type']})")

        # 결과 데이터 출력 (최대 5행)
        print("\n데이터:")
        for row in execution_result['rows'][:5]:
            print(row)
````

### 쿼리 상태 확인

```python
import requests
import time

def check_query_status(access_token, query_id):
    """실행 중인 쿼리의 상태 확인"""
    url = f"http://localhost:8000/api/query/status/{query_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"쿼리 상태 확인 실패: {response.status_code}")
        return None

# 사용 예제 - 장시간 실행 쿼리의 상태 모니터링
def execute_long_query(access_token, sql, db_id=None):
    """장시간 실행 쿼리 실행 및 모니터링"""
    # 쿼리 실행 요청
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": sql,
        "timeout": 300  # 5분 타임아웃
    }
    if db_id:
        data["db_id"] = db_id

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"쿼리 실행 요청 실패: {response.status_code}")
        return None

    result = response.json()
    query_id = result["query_id"]

    # 쿼리가 즉시 완료된 경우
    if result["status"] == "completed":
        return result

    # 쿼리 상태 모니터링
    print("쿼리 실행 중...")
    while True:
        status = check_query_status(access_token, query_id)

        if not status:
            print("상태 확인 실패")
            break

        if status["status"] in ["completed", "failed", "cancelled"]:
            # 쿼리 완료, 결과 조회
            if status["status"] == "completed":
                result_url = f"http://localhost:8000/api/result/{status['result_id']}"
                result_response = requests.get(result_url, headers=headers)
                if result_response.status_code == 200:
                    return result_response.json()

            # 쿼리 실패 또는 취소
            return status

        # 진행 상황 출력
        print(f"진행률: {status.get('progress', '?')}%, 경과 시간: {status.get('elapsed_time', '?')}초")
        time.sleep(2)  # 2초마다 상태 확인

# 사용 예제
long_query = """
SELECT c.CustomerName, COUNT(o.OrderID) AS OrderCount, SUM(od.Quantity * p.Price) AS TotalAmount
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderDetails od ON o.OrderID = od.OrderID
JOIN Products p ON od.ProductID = p.ProductID
WHERE o.OrderDate BETWEEN '2022-01-01' AND '2022-12-31'
GROUP BY c.CustomerName
ORDER BY TotalAmount DESC
"""

result = execute_long_query(access_token, long_query)
if result:
    print("쿼리 실행 완료!")
    # 결과 처리
```

### 쿼리 취소

````python
import requests

def cancel_query(access_token, query_id):
    """실행 중인 쿼리 취소"""
    url = f"http://localhost:8000/api/query/cancel/{query_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"쿼리 취소 실패: {response.status_code}")
        return None

# 사용 예제
cancel_result = cancel_query(access_token, "query_12345")
if cancel_result:
    print(f"쿼리 취소 상태: {cancel_result['status']}")
    print(f"메시지: {cancel_result['message']}")
```## 5. 결
과 처리 및 분석

### 쿼리 결과 조회

```python
import requests

def get_query_result(access_token, result_id, page=1, page_size=100):
    """쿼리 결과 조회"""
    url = f"http://localhost:8000/api/result/{result_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "page": page,
        "page_size": page_size
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"결과 조회 실패: {response.status_code}")
        return None

# 사용 예제
if execution_result and "result_id" in execution_result:
    result_id = execution_result["result_id"]

    # 첫 페이지 조회
    result_page1 = get_query_result(access_token, result_id, page=1, page_size=10)

    if result_page1:
        print(f"총 행 수: {result_page1['total_row_count']}")
        print(f"총 페이지 수: {result_page1['total_pages']}")

        # 결과 데이터 출력
        print("\n결과 데이터 (페이지 1):")
        for row in result_page1['rows']:
            print(row)

        # 두 번째 페이지가 있으면 조회
        if result_page1['total_pages'] > 1:
            result_page2 = get_query_result(access_token, result_id, page=2, page_size=10)
            if result_page2:
                print("\n결과 데이터 (페이지 2):")
                for row in result_page2['rows']:
                    print(row)
````

### 결과 요약 생성

```python
import requests

def generate_result_summary(access_token, result_id, detail_level="medium"):
    """쿼리 결과에 대한 자연어 요약 생성"""
    url = f"http://localhost:8000/api/result/{result_id}/summary"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "detail_level": detail_level  # "low", "medium", "high" 중 하나
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"요약 생성 실패: {response.status_code}")
        return None

# 사용 예제
if execution_result and "result_id" in execution_result:
    result_id = execution_result["result_id"]

    summary = generate_result_summary(access_token, result_id, detail_level="high")

    if summary:
        print("\n결과 요약:")
        print(summary["summary"])

        print("\n주요 인사이트:")
        for insight in summary["insights"]:
            print(f"- {insight}")
```

### 리포트 생성 및 조회

````python
import requests
import time

def generate_report(access_token, result_id, report_type="standard", visualizations=None, include_code=False):
    """쿼리 결과를 기반으로 데이터 분석 리포트 생성"""
    url = f"http://localhost:8000/api/result/{result_id}/report"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "report_type": report_type,
        "include_code": include_code
    }
    if visualizations:
        data["visualizations"] = visualizations

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"리포트 생성 요청 실패: {response.status_code}")
        return None

def check_report_status(access_token, report_id):
    """리포트 생성 상태 확인"""
    url = f"http://localhost:8000/api/report/{report_id}/status"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"리포트 상태 확인 실패: {response.status_code}")
        return None

def get_report(access_token, report_id):
    """생성된 리포트 조회"""
    url = f"http://localhost:8000/api/report/{report_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"리포트 조회 실패: {response.status_code}")
        return None

# 사용 예제
if execution_result and "result_id" in execution_result:
    result_id = execution_result["result_id"]

    # 리포트 생성 요청
    report_request = generate_report(
        access_token,
        result_id,
        report_type="comprehensive",
        visualizations=["bar", "pie", "line"],
        include_code=True
    )

    if report_request:
        report_id = report_request["report_id"]
        print(f"리포트 생성 요청 완료 (ID: {report_id})")
        print(f"예상 완료 시간: {report_request['estimated_completion_time']}")

        # 리포트 생성 상태 확인
        while True:
            status = check_report_status(access_token, report_id)

            if not status:
                print("상태 확인 실패")
                break

            print(f"상태: {status['status']}, 진행률: {status['progress']}%")

            if status["status"] == "completed":
                # 리포트 조회
                report = get_report(access_token, report_id)

                if report:
                    print("\n리포트 생성 완료!")
                    print(f"제목: {report['title']}")
                    print(f"요약: {report['summary']}")

                    print("\n인사이트:")
                    for insight in report["insights"]:
                        print(f"- {insight}")

                    print(f"\n시각화: {len(report['visualizations'])}개")
                    for viz in report["visualizations"]:
                        print(f"- {viz['type']}: {viz['title']}")

                    # 리포트 다운로드
                    download_url = f"http://localhost:8000/api/report/{report_id}/download?format=pdf"
                    download_response = requests.get(
                        download_url,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if download_response.status_code == 200:
                        with open("report.pdf", "wb") as f:
                            f.write(download_response.content)
                        print("\nPDF 리포트가 'report.pdf'로 저장되었습니다.")

                break

            elif status["status"] == "failed":
                print(f"리포트 생성 실패: {status.get('message', '알 수 없는 오류')}")
                break

            time.sleep(2)  # 2초마다 상태 확인
```## 6. 이
력 관리 및 공유

### 쿼리 이력 조회

```python
import requests

def get_query_history(access_token, page=1, page_size=20, sort_by="created_at", sort_order="desc", filter_favorite=False, filter_tag=None, search=None):
    """쿼리 이력 조회"""
    url = "http://localhost:8000/api/history"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

    if filter_favorite:
        params["filter_favorite"] = "true"

    if filter_tag:
        params["filter_tag"] = filter_tag

    if search:
        params["search"] = search

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"이력 조회 실패: {response.status_code}")
        return None

# 사용 예제
history = get_query_history(
    access_token,
    page=1,
    page_size=10,
    sort_by="created_at",
    sort_order="desc",
    filter_favorite=True
)

if history:
    print(f"총 이력 수: {history['total_count']}")
    print(f"페이지: {history['page']}/{history['total_pages']}")

    print("\n쿼리 이력:")
    for item in history["history"]:
        print(f"- ID: {item['id']}")
        print(f"  질의: {item['natural_language']}")
        print(f"  DB: {item['db_name']}")
        print(f"  상태: {item['status']}")
        print(f"  생성 시간: {item['created_at']}")
        print(f"  태그: {', '.join(item['tags'])}")
        print()
````

### 쿼리 이력 즐겨찾기 및 태그 관리

```python
import requests

def update_favorite(access_token, history_id, favorite):
    """쿼리 이력 즐겨찾기 설정/해제"""
    url = f"http://localhost:8000/api/history/{history_id}/favorite"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "favorite": favorite
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"즐겨찾기 업데이트 실패: {response.status_code}")
        return None

def update_tags(access_token, history_id, tags):
    """쿼리 이력 태그 업데이트"""
    url = f"http://localhost:8000/api/history/{history_id}/tags"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "tags": tags
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"태그 업데이트 실패: {response.status_code}")
        return None

def update_notes(access_token, history_id, notes):
    """쿼리 이력 노트 업데이트"""
    url = f"http://localhost:8000/api/history/{history_id}/notes"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "notes": notes
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"노트 업데이트 실패: {response.status_code}")
        return None

# 사용 예제
if history and history["history"]:
    history_id = history["history"][0]["id"]

    # 즐겨찾기 설정
    favorite_result = update_favorite(access_token, history_id, True)
    if favorite_result:
        print(f"즐겨찾기 설정 완료: {favorite_result['message']}")

    # 태그 업데이트
    tags_result = update_tags(access_token, history_id, ["monthly-report", "sales", "important"])
    if tags_result:
        print(f"태그 업데이트 완료: {tags_result['message']}")
        print(f"새 태그: {', '.join(tags_result['tags'])}")

    # 노트 업데이트
    notes_result = update_notes(access_token, history_id, "월간 판매 보고서용 쿼리 - 경영진 회의 자료로 사용")
    if notes_result:
        print(f"노트 업데이트 완료: {notes_result['message']}")
```

### 쿼리 재실행

```python
import requests

def rerun_query(access_token, history_id, use_original_sql=True, db_id=None):
    """이전에 실행한 쿼리 재실행"""
    url = f"http://localhost:8000/api/history/{history_id}/rerun"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "use_original_sql": use_original_sql
    }
    if db_id:
        data["db_id"] = db_id

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"쿼리 재실행 실패: {response.status_code}")
        return None

# 사용 예제
if history and history["history"]:
    history_id = history["history"][0]["id"]

    rerun_result = rerun_query(access_token, history_id)
    if rerun_result:
        print(f"쿼리 재실행 요청 완료: {rerun_result['message']}")
        print(f"새 쿼리 ID: {rerun_result['query_id']}")
        print(f"새 결과 ID: {rerun_result['result_id']}")
```

### 쿼리 공유

````python
import requests

def create_share_link(access_token, history_id, expires_in=7, allowed_users=None, include_result=True, include_report=False):
    """쿼리 및 결과에 대한 공유 링크 생성"""
    url = "http://localhost:8000/api/share"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "history_id": history_id,
        "expires_in": expires_in,
        "include_result": include_result,
        "include_report": include_report
    }
    if allowed_users:
        data["allowed_users"] = allowed_users

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"공유 링크 생성 실패: {response.status_code}")
        return None

def get_share_links(access_token):
    """사용자가 생성한 공유 링크 목록 조회"""
    url = "http://localhost:8000/api/share"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"공유 링크 목록 조회 실패: {response.status_code}")
        return None

def delete_share_link(access_token, share_id):
    """공유 링크 삭제"""
    url = f"http://localhost:8000/api/share/{share_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"공유 링크 삭제 실패: {response.status_code}")
        return None

# 사용 예제
if history and history["history"]:
    history_id = history["history"][0]["id"]

    # 공유 링크 생성
    share_result = create_share_link(
        access_token,
        history_id,
        expires_in=14,
        allowed_users=["colleague@example.com"],
        include_result=True,
        include_report=True
    )

    if share_result:
        print(f"공유 링크 생성 완료!")
        print(f"공유 URL: {share_result['share_url']}")
        print(f"만료 시간: {share_result['expires_at']}")

        # 공유 링크 목록 조회
        shares = get_share_links(access_token)
        if shares:
            print(f"\n공유 링크 목록: {len(shares['shares'])}개")
            for share in shares["shares"]:
                print(f"- ID: {share['share_id']}")
                print(f"  URL: {share['share_url']}")
                print(f"  생성 시간: {share['created_at']}")
                print(f"  만료 시간: {share['expires_at']}")
                print(f"  접근 횟수: {share['access_count']}")
                print()

        # 공유 링크 삭제
        delete_result = delete_share_link(access_token, share_result['share_id'])
        if delete_result:
            print(f"공유 링크 삭제 완료: {delete_result['message']}")
```## 7
. 오류 처리

### 기본 오류 처리

```python
import requests

def handle_api_error(response):
    """API 오류 응답 처리"""
    try:
        error_data = response.json()
        error_code = error_data.get("code", "UNKNOWN_ERROR")
        error_message = error_data.get("message", "알 수 없는 오류가 발생했습니다.")
        suggestions = error_data.get("suggestions", [])

        print(f"오류 코드: {error_code}")
        print(f"오류 메시지: {error_message}")

        if suggestions:
            print("제안 사항:")
            for suggestion in suggestions:
                print(f"- {suggestion}")

        return error_data
    except ValueError:
        print(f"오류 응답 파싱 실패: {response.text}")
        return {"code": "PARSE_ERROR", "message": response.text}

# 사용 예제
def safe_api_call(func, *args, **kwargs):
    """안전한 API 호출 래퍼"""
    try:
        response = func(*args, **kwargs)

        if response.status_code >= 400:
            error_data = handle_api_error(response)
            return {"success": False, "error": error_data}

        return {"success": True, "data": response.json()}

    except requests.RequestException as e:
        print(f"API 요청 실패: {e}")
        return {"success": False, "error": {"code": "REQUEST_ERROR", "message": str(e)}}

# 예제 API 호출
def execute_query(access_token, sql, db_id=None):
    url = "http://localhost:8000/api/query/execute"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "sql": sql,
        "db_id": db_id
    }

    return requests.post(url, headers=headers, json=data)

# 안전한 API 호출 사용
result = safe_api_call(
    execute_query,
    access_token,
    "SELECT * FROM NonExistentTable",
    "mssql-prod-01"
)

if result["success"]:
    print("쿼리 실행 성공!")
    # 결과 처리
else:
    error = result["error"]
    print(f"쿼리 실행 실패: {error['message']}")

    # 특정 오류 코드에 따른 처리
    if error["code"] == "QUERY_SYNTAX_ERROR":
        print("SQL 구문을 확인하세요.")
    elif error["code"] == "DB_TABLE_NOT_FOUND":
        print("테이블 이름을 확인하세요.")
````

### 재시도 로직

```python
import requests
import time

def api_call_with_retry(func, max_retries=3, retry_delay=2, retryable_codes=None, *args, **kwargs):
    """재시도 로직이 포함된 API 호출 함수"""
    if retryable_codes is None:
        retryable_codes = [
            "DB_CONNECTION_ERROR",
            "DB_TIMEOUT",
            "QUERY_TIMEOUT",
            "LLM_SERVICE_ERROR",
            "SYSTEM_OVERLOADED"
        ]

    retries = 0
    while retries < max_retries:
        try:
            response = func(*args, **kwargs)

            if response.status_code == 200:
                return {"success": True, "data": response.json()}

            error_data = response.json()
            error_code = error_data.get("code", "UNKNOWN_ERROR")

            # 재시도 가능한 오류인 경우
            if error_data.get("retryable", False) or error_code in retryable_codes:
                retries += 1
                wait_time = retry_delay * (2 ** (retries - 1))  # 지수 백오프
                print(f"재시도 가능한 오류 발생: {error_code}. {wait_time}초 후 재시도 ({retries}/{max_retries})...")
                time.sleep(wait_time)
                continue

            # 재시도할 수 없는 오류
            return {"success": False, "error": error_data}

        except requests.RequestException as e:
            retries += 1
            wait_time = retry_delay * (2 ** (retries - 1))
            print(f"요청 실패: {e}. {wait_time}초 후 재시도 ({retries}/{max_retries})...")
            time.sleep(wait_time)

    return {"success": False, "error": {"code": "MAX_RETRIES_EXCEEDED", "message": "최대 재시도 횟수를 초과했습니다."}}

# 사용 예제
result = api_call_with_retry(
    execute_query,
    max_retries=5,
    retry_delay=1,
    access_token=access_token,
    sql="SELECT TOP 10 * FROM Products",
    db_id="mssql-prod-01"
)

if result["success"]:
    print("쿼리 실행 성공!")
    # 결과 처리
else:
    print(f"쿼리 실행 실패: {result['error']['message']}")
```

### 오류 로깅

````python
import logging
import requests
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="api_client.log"
)
logger = logging.getLogger("api_client")

def log_api_call(request_method, url, headers, data=None, params=None, response=None, error=None):
    """API 호출 로깅"""
    # 민감 정보 마스킹
    safe_headers = headers.copy() if headers else {}
    if "Authorization" in safe_headers:
        safe_headers["Authorization"] = "Bearer [REDACTED]"

    log_data = {
        "request": {
            "method": request_method,
            "url": url,
            "headers": safe_headers
        }
    }

    if data:
        # 민감 정보가 있을 수 있는 필드 마스킹
        safe_data = data.copy() if isinstance(data, dict) else data
        if isinstance(safe_data, dict) and "password" in safe_data:
            safe_data["password"] = "[REDACTED]"
        log_data["request"]["data"] = safe_data

    if params:
        log_data["request"]["params"] = params

    if response:
        log_data["response"] = {
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type")
        }

        # 응답 본문이 JSON인 경우만 로깅
        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                log_data["response"]["body"] = response.json()
            except ValueError:
                log_data["response"]["body"] = "[PARSE_ERROR]"

    if error:
        log_data["error"] = str(error)

    # 로그 레벨 결정
    if error or (response and response.status_code >= 500):
        logger.error(json.dumps(log_data))
    elif response and response.status_code >= 400:
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))

# 로깅이 포함된 API 호출 함수
def logged_api_call(method, url, headers=None, data=None, params=None, json_data=None):
    """로깅이 포함된 API 호출 함수"""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            json=json_data
        )

        log_api_call(
            request_method=method,
            url=url,
            headers=headers,
            data=json_data if json_data else data,
            params=params,
            response=response
        )

        return response

    except requests.RequestException as e:
        log_api_call(
            request_method=method,
            url=url,
            headers=headers,
            data=json_data if json_data else data,
            params=params,
            error=e
        )
        raise

# 사용 예제
try:
    response = logged_api_call(
        method="POST",
        url="http://localhost:8000/api/query/execute",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json_data={
            "sql": "SELECT TOP 10 * FROM Products",
            "db_id": "mssql-prod-01"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print("쿼리 실행 성공!")
        # 결과 처리
    else:
        print(f"쿼리 실행 실패: {response.status_code}")
        try:
            error_data = response.json()
            print(f"오류: {error_data.get('message', '알 수 없는 오류')}")
        except:
            print(f"응답: {response.text}")

except requests.RequestException as e:
    print(f"API 요청 실패: {e}")
```##
 8. 관리자 기능

### 사용자 관리

```python
import requests

def get_users(access_token, page=1, page_size=20, sort_by="username", sort_order="asc", search=None):
    """사용자 목록 조회"""
    url = "http://localhost:8000/api/admin/users"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

    if search:
        params["search"] = search

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"사용자 목록 조회 실패: {response.status_code}")
        return None

def get_user_details(access_token, user_id):
    """사용자 상세 정보 조회"""
    url = f"http://localhost:8000/api/admin/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"사용자 상세 정보 조회 실패: {response.status_code}")
        return None

def create_user(access_token, username, email, password, role="user", permissions=None):
    """새로운 사용자 생성"""
    url = "http://localhost:8000/api/admin/users"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }

    if permissions:
        data["permissions"] = permissions

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"사용자 생성 실패: {response.status_code}")
        return None

def update_user(access_token, user_id, email=None, role=None, status=None, permissions=None):
    """사용자 정보 업데이트"""
    url = f"http://localhost:8000/api/admin/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {}

    if email:
        data["email"] = email

    if role:
        data["role"] = role

    if status:
        data["status"] = status

    if permissions:
        data["permissions"] = permissions

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"사용자 업데이트 실패: {response.status_code}")
        return None

# 사용 예제
# 관리자 권한이 있는 토큰 필요
admin_token = login("admin", "admin_password")

if admin_token:
    # 사용자 목록 조회
    users = get_users(admin_token)
    if users:
        print(f"총 사용자 수: {users['total_count']}")
        print(f"페이지: {users['page']}/{users['total_pages']}")

        print("\n사용자 목록:")
        for user in users["users"]:
            print(f"- ID: {user['id']}")
            print(f"  사용자명: {user['username']}")
            print(f"  이메일: {user['email']}")
            print(f"  역할: {user['role']}")
            print(f"  상태: {user['status']}")
            print()

    # 새 사용자 생성
    new_user = create_user(
        admin_token,
        username="newuser",
        email="newuser@example.com",
        password="securepassword",
        role="user",
        permissions={
            "allowed_databases": [
                {
                    "db_id": "mssql-prod-01",
                    "allowed_schemas": ["dbo", "sales"],
                    "allowed_tables": ["Products", "Orders"]
                }
            ]
        }
    )

    if new_user:
        print(f"새 사용자 생성 완료: {new_user['username']} (ID: {new_user['id']})")

        # 사용자 정보 업데이트
        update_result = update_user(
            admin_token,
            new_user['id'],
            email="updated@example.com",
            role="admin"
        )

        if update_result:
            print(f"사용자 정보 업데이트 완료: {update_result['message']}")
````

### 정책 관리

```python
import requests

def get_policies(access_token):
    """정책 목록 조회"""
    url = "http://localhost:8000/api/admin/policies"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"정책 목록 조회 실패: {response.status_code}")
        return None

def update_policy(access_token, policy_id, name=None, description=None, settings=None):
    """정책 업데이트"""
    url = f"http://localhost:8000/api/admin/policies/{policy_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {}

    if name:
        data["name"] = name

    if description:
        data["description"] = description

    if settings:
        data["settings"] = settings

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"정책 업데이트 실패: {response.status_code}")
        return None

# 사용 예제
if admin_token:
    # 정책 목록 조회
    policies = get_policies(admin_token)
    if policies:
        print("\n정책 목록:")
        for policy in policies["policies"]:
            print(f"- ID: {policy['id']}")
            print(f"  이름: {policy['name']}")
            print(f"  설명: {policy['description']}")
            print(f"  설정:")
            for key, value in policy["settings"].items():
                print(f"    - {key}: {value}")
            print()

    # 정책 업데이트
    policy_update = update_policy(
        admin_token,
        "policy_default",
        name="기본 정책",
        description="일반 사용자에게 적용되는 기본 정책",
        settings={
            "max_queries_per_day": 200,
            "max_query_execution_time": 120,
            "max_result_size": 20000,
            "allowed_query_types": ["SELECT"],
            "blocked_keywords": ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]
        }
    )

    if policy_update:
        print(f"정책 업데이트 완료: {policy_update['message']}")
```

### 시스템 모니터링

```python
import requests

def get_system_statistics(access_token, period="last_30_days", group_by="day"):
    """시스템 사용 통계 조회"""
    url = "http://localhost:8000/api/admin/statistics"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "period": period,
        "group_by": group_by
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"시스템 통계 조회 실패: {response.status_code}")
        return None

def get_system_logs(access_token, page=1, page_size=100, level=None, category=None, start_date=None, end_date=None, user_id=None, search=None):
    """시스템 로그 조회"""
    url = "http://localhost:8000/api/admin/logs"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "page": page,
        "page_size": page_size
    }

    if level:
        params["level"] = level

    if category:
        params["category"] = category

    if start_date:
        params["start_date"] = start_date

    if end_date:
        params["end_date"] = end_date

    if user_id:
        params["user_id"] = user_id

    if search:
        params["search"] = search

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"시스템 로그 조회 실패: {response.status_code}")
        return None

# 사용 예제
if admin_token:
    # 시스템 통계 조회
    stats = get_system_statistics(admin_token, period="last_7_days", group_by="day")
    if stats:
        print("\n시스템 통계:")
        print(f"기간: {stats['period']}")
        print(f"총 쿼리 수: {stats['total_queries']}")
        print(f"총 사용자 수: {stats['total_users']}")
        print(f"활성 사용자 수: {stats['active_users']}")
        print(f"평균 쿼리 시간: {stats['average_query_time']}초")
        print(f"쿼리 성공률: {stats['query_success_rate']}%")

        print("\n상위 사용자:")
        for user in stats["top_users"][:3]:
            print(f"- {user['username']}: {user['query_count']}회")

        print("\n상위 데이터베이스:")
        for db in stats["top_databases"][:3]:
            print(f"- {db['db_name']}: {db['query_count']}회")

    # 시스템 로그 조회
    logs = get_system_logs(
        admin_token,
        page=1,
        page_size=10,
        level="error",
        category="query",
        start_date="2023-01-01T00:00:00Z"
    )

    if logs:
        print(f"\n시스템 로그 (총 {logs['total_count']}개):")
        for log in logs["logs"]:
            print(f"- 시간: {log['timestamp']}")
            print(f"  레벨: {log['level']}")
            print(f"  카테고리: {log['category']}")
            print(f"  메시지: {log['message']}")
            print(f"  사용자: {log.get('username', 'N/A')}")
            print()
```

### 시스템 설정 관리

```python
import requests

def get_system_settings(access_token):
    """시스템 설정 조회"""
    url = "http://localhost:8000/api/admin/system/settings"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"시스템 설정 조회 실패: {response.status_code}")
        return None

def update_system_settings(access_token, settings):
    """시스템 설정 업데이트"""
    url = "http://localhost:8000/api/admin/system/settings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "settings": settings
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"시스템 설정 업데이트 실패: {response.status_code}")
        return None

# 사용 예제
if admin_token:
    # 시스템 설정 조회
    settings = get_system_settings(admin_token)
    if settings:
        print("\n시스템 설정:")
        print(f"시스템 이름: {settings['settings']['general']['system_name']}")
        print(f"유지보수 모드: {settings['settings']['general']['maintenance_mode']}")
        print(f"세션 타임아웃: {settings['settings']['security']['session_timeout']}초")
        print(f"LLM 제공자: {settings['settings']['llm']['provider']}")
        print(f"LLM 모델: {settings['settings']['llm']['model']}")

    # 시스템 설정 업데이트
    update_result = update_system_settings(
        admin_token,
        {
            "general": {
                "system_name": "SQL DB LLM Agent Pro",
                "maintenance_mode": False
            },
            "security": {
                "session_timeout": 1800
            },
            "llm": {
                "provider": "azure-openai",
                "model": "gpt-4-turbo",
                "temperature": 0.2
            }
        }
    )

    if update_result:
        print(f"시스템 설정 업데이트 완료: {update_result['message']}")
```

## 결론

이 문서에서는 SQL DB LLM Agent API의 주요 기능을 사용하는 방법에 대한 예제 코드를 제공했습니다. 이 예제들을 참고하여 자신의 애플리케이션에 API를 통합할 수 있습니다. 더 자세한 정보는 API 문서를 참조하세요.

API를 사용하면서 문제가 발생하거나 추가 지원이 필요한 경우, 관리자에게 문의하세요.
