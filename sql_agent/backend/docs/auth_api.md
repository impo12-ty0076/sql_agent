# 인증 API

인증 API는 사용자 인증, 로그아웃, 현재 사용자 정보 조회 등의 기능을 제공합니다.

## 엔드포인트

### 로그인

```
POST /api/auth/login
```

사용자 인증 및 액세스 토큰 발급

#### 요청 본문

```json
{
  "username": "string",
  "password": "string"
}
```

또는 `application/x-www-form-urlencoded` 형식:

- `username`: 사용자 이름
- `password`: 비밀번호

#### 응답

**성공 (200 OK)**

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "user",
    "last_login": "2023-01-01T00:00:00Z"
  }
}
```

**실패 (401 Unauthorized)**

```json
{
  "detail": "잘못된 사용자 이름 또는 비밀번호"
}
```

### 로그아웃

```
POST /api/auth/logout
```

현재 세션을 무효화합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "message": "성공적으로 로그아웃되었습니다."
}
```

**실패 (401 Unauthorized)**

```json
{
  "detail": "인증되지 않은 요청"
}
```

### 현재 사용자 정보 조회

```
GET /api/auth/me
```

현재 인증된 사용자의 정보를 반환합니다.

#### 요청 헤더

- `Authorization`: `Bearer {token}`

#### 응답

**성공 (200 OK)**

```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "role": "user",
  "last_login": "2023-01-01T00:00:00Z",
  "preferences": {
    "default_db": "string",
    "theme": "light",
    "results_per_page": 10
  }
}
```

**실패 (401 Unauthorized)**

```json
{
  "detail": "인증되지 않은 요청"
}
```

## 사용 예제

### 로그인 및 토큰 획득

```python
import requests

url = "http://localhost:8000/api/auth/login"
data = {
    "username": "user",
    "password": "password"
}

response = requests.post(url, data=data)
token_data = response.json()

# 토큰 저장
access_token = token_data["access_token"]
```

### 현재 사용자 정보 조회

```python
import requests

url = "http://localhost:8000/api/auth/me"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)
user_data = response.json()
```

### 로그아웃

```python
import requests

url = "http://localhost:8000/api/auth/logout"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.post(url, headers=headers)
```