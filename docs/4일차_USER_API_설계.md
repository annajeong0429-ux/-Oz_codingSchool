# 4일차 - User API 설계 명세서

---

## API 목록

| No | API 이름 | 메서드 | 엔드포인트 | 인증 필요 |
|----|---------|--------|-----------|---------|
| 1 | 회원가입 | POST | `/api/v1/auth/register/` | N |
| 2 | 로그인 | POST | `/api/v1/auth/login/` | N |
| 3 | 로그아웃 | POST | `/api/v1/auth/logout/` | Y |
| 4 | 내 정보 조회 | GET | `/api/v1/users/me/` | Y |
| 5 | 내 정보 수정 | PATCH | `/api/v1/users/me/` | Y |
| 6 | 회원 탈퇴 | DELETE | `/api/v1/users/me/` | Y |

---

## 1. 회원가입 API

### 1-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 회원가입 API |
| 설명 | 이메일, 비밀번호, 이름을 입력받아 신규 사용자를 등록하는 API |
| 엔드포인트 | `/api/v1/auth/register/` |
| 메서드 | `POST` |
| 인증 필요 여부 | N |

### 1-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Content-Type | application/json | 요청 타입 |

#### 본문 예시

```json
{
  "email": "example@example.com",
  "password": "Password1234!",
  "name": "홍길동"
}
```

#### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
|-----------|------|------|------|
| email | string | Y | 사용자 이메일 (최대 30자, 중복 불가) |
| password | string | Y | 비밀번호 (대소문자+특수문자 포함, 8~20자) |
| name | string | Y | 사용자 이름 (2~10글자) |

### 1-3. 응답(Response)

#### 성공 - 201 Created

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "홍길동",
  "created_at": "2025-01-01T00:00:00"
}
```

| 필드명 | 타입 | 설명 |
|--------|------|------|
| id | integer | 사용자 고유 ID |
| email | string | 사용자 이메일 |
| name | string | 사용자 이름 |
| created_at | string | 가입일시 |

#### 실패

- **400 Bad Request**

```json
{
  "detail": "이미 사용 중인 이메일입니다."
}
```

| 에러 코드 | 설명 |
|----------|------|
| duplicate_email | 이미 가입된 이메일인 경우 |
| invalid_password | 비밀번호 형식이 올바르지 않은 경우 |
| empty_fields | 필수 필드가 비어있는 경우 |

### 1-4. 비고
- 비밀번호는 평문이 아닌 암호화된 형태(argon2)로 저장됩니다.
- 이메일 형식은 정규표현식으로 검증합니다.

---

## 2. 로그인 API

### 2-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 사용자 로그인 API |
| 설명 | 이메일, 비밀번호를 활용한 로그인 API |
| 엔드포인트 | `/api/v1/auth/login/` |
| 메서드 | `POST` |
| 인증 필요 여부 | N |

### 2-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Content-Type | application/json | 요청 타입 |

#### 본문 예시

```json
{
  "email": "example@example.com",
  "password": "securepassword"
}
```

#### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
|-----------|------|------|------|
| email | string | Y | 사용자 이메일 |
| password | string | Y | 사용자 비밀번호 |

### 2-3. 응답(Response)

#### 성공 - 200 OK

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": 1,
    "email": "example@example.com",
    "name": "홍길동"
  }
}
```

| 필드명 | 타입 | 설명 |
|--------|------|------|
| access_token | string | JWT 액세스 토큰 |
| refresh_token | string | JWT 리프레시 토큰 |
| user | object | 사용자 정보 |

#### 실패

- **400 Bad Request**

```json
{
  "detail": "이메일 또는 비밀번호가 일치하지 않습니다."
}
```

| 에러 코드 | 설명 |
|----------|------|
| invalid_email_or_password | 이메일 혹은 비밀번호가 잘못된 경우 |
| empty_fields | 필수 필드 중 하나라도 비어있는 경우 |

### 2-4. 비고
- JWT 토큰은 이후 모든 인증이 필요한 API 호출 시 사용됩니다.
- 비밀번호는 평문이 아닌 암호화된 형태로 저장되어야 합니다.

---

## 3. 로그아웃 API

### 3-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 로그아웃 API |
| 설명 | 현재 로그인된 사용자의 토큰을 무효화하는 API |
| 엔드포인트 | `/api/v1/auth/logout/` |
| 메서드 | `POST` |
| 인증 필요 여부 | Y |

### 3-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Content-Type | application/json | 요청 타입 |
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

#### 본문 예시

```json
{
  "refresh_token": "string"
}
```

#### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
|-----------|------|------|------|
| refresh_token | string | Y | JWT 리프레시 토큰 |

### 3-3. 응답(Response)

#### 성공 - 200 OK

```json
{
  "message": "로그아웃 되었습니다."
}
```

#### 실패

- **401 Unauthorized**

```json
{
  "detail": "인증이 필요합니다."
}
```

---

## 4. 내 정보 조회 API

### 4-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 내 정보 조회 API |
| 설명 | 현재 로그인된 사용자의 정보를 조회하는 API |
| 엔드포인트 | `/api/v1/users/me/` |
| 메서드 | `GET` |
| 인증 필요 여부 | Y |

### 4-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

### 4-3. 응답(Response)

#### 성공 - 200 OK

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "홍길동",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

| 필드명 | 타입 | 설명 |
|--------|------|------|
| id | integer | 사용자 고유 ID |
| email | string | 사용자 이메일 |
| name | string | 사용자 이름 |
| created_at | string | 가입일시 |
| updated_at | string | 정보 수정일시 |

#### 실패

- **401 Unauthorized**

```json
{
  "detail": "인증이 필요합니다."
}
```

---

## 5. 내 정보 수정 API

### 5-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 내 정보 수정 API |
| 설명 | 현재 로그인된 사용자의 정보를 수정하는 API |
| 엔드포인트 | `/api/v1/users/me/` |
| 메서드 | `PATCH` |
| 인증 필요 여부 | Y |

### 5-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Content-Type | application/json | 요청 타입 |
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

#### 본문 예시

```json
{
  "name": "새이름",
  "password": "NewPassword1234!"
}
```

#### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
|-----------|------|------|------|
| name | string | N | 변경할 이름 (2~10글자) |
| password | string | N | 변경할 비밀번호 (대소문자+특수문자 포함, 8~20자) |

### 5-3. 응답(Response)

#### 성공 - 200 OK

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "새이름",
  "updated_at": "2025-01-01T00:00:00"
}
```

#### 실패

- **400 Bad Request**

```json
{
  "detail": "수정할 항목을 입력해주세요."
}
```

| 에러 코드 | 설명 |
|----------|------|
| empty_fields | 수정할 항목이 하나도 없는 경우 |
| invalid_password | 비밀번호 형식이 올바르지 않은 경우 |

---

## 6. 회원 탈퇴 API

### 6-1. API 개요

| 항목 | 내용 |
|------|------|
| API 이름 | 회원 탈퇴 API |
| 설명 | 현재 로그인된 사용자의 계정을 삭제하는 API |
| 엔드포인트 | `/api/v1/users/me/` |
| 메서드 | `DELETE` |
| 인증 필요 여부 | Y |

### 6-2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|-----|-------|------|
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

#### 본문 예시

```json
{
  "password": "CurrentPassword1234!"
}
```

#### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
|-----------|------|------|------|
| password | string | Y | 현재 비밀번호 (본인 확인용) |

### 6-3. 응답(Response)

#### 성공 - 200 OK

```json
{
  "message": "회원 탈퇴가 완료되었습니다."
}
```

#### 실패

- **400 Bad Request**

```json
{
  "detail": "비밀번호가 일치하지 않습니다."
}
```

### 6-4. 비고
- 탈퇴 시 관련 데이터(환자 기록 등)는 보존됩니다.

---

## 공통 에러 응답

| HTTP 상태 코드 | 설명 |
|--------------|------|
| 400 Bad Request | 잘못된 요청 (입력값 오류) |
| 401 Unauthorized | 인증 실패 (토큰 없음 또는 만료) |
| 403 Forbidden | 권한 없음 |
| 404 Not Found | 리소스를 찾을 수 없음 |
| 500 Internal Server Error | 서버 내부 오류 |
