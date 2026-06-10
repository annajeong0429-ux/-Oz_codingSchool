# 6일차 - AI 폐렴 예측 API 설계 명세서

> 본 문서는 `app/worker/model.py`의 `predict_pneumonia()` 함수와 ConvNeXt-Tiny + DenseNet121 OR 앙상블 모델을 기준으로 작성한 API 명세입니다.

---

## 1. 개요 & 공통 규칙

- **Base URL**: `/api/v1`
- **인증**: 로그인된 사용자(의료 실무진)만 호출 가능. JWT 토큰 필요.
- **데이터 형식**: X-Ray 이미지 업로드는 `multipart/form-data`, 응답은 JSON.
- **공통 상태 코드**
  - `200 OK` 조회 성공 / `201 Created` 등록 성공
  - `400 Bad Request` 입력값 오류 / `401 Unauthorized` 인증 실패
  - `404 Not Found` 존재하지 않는 ID / `422 Unprocessable Entity` 입력값 검증 실패
  - `500 Internal Server Error` 서버 내부 오류 (모델 로딩 실패 등)

---

## 2. 엔드포인트 요약

| No | 기능 | 메서드 | 엔드포인트 |
|---|---|---|---|
| 1 | AI 폐렴 예측 요청 | POST | `/api/v1/ai/predict` |
| 2 | 예측 결과 단건 조회 | GET | `/api/v1/ai/results/{result_id}` |
| 3 | 예측 결과 목록 조회 | GET | `/api/v1/ai/results` |

---

## 3. AI 폐렴 예측 API

### 3.1 AI 폐렴 예측 요청 — `POST /api/v1/ai/predict`

#### 개요

| 항목 | 내용 |
|------|------|
| 설명 | X-Ray 이미지를 업로드하면 AI 모델이 폐렴 여부를 판독하고 결과를 반환하는 API |
| 메서드 | POST |
| 엔드포인트 | `/api/v1/ai/predict` |
| Content-Type | `multipart/form-data` |
| 인증 필요 | Y |

#### 요청(Request)

**Headers**

| Key | Value | 설명 |
|-----|-------|------|
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |
| Content-Type | multipart/form-data | 파일 업로드 |

**Form Fields**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| xray_image | file | ✅ | 흉부 X-Ray 이미지 파일 (JPEG, PNG) |
| record_id | integer | ✅ | 연결할 진료기록 ID (medical_records.id) |

#### 응답(Response)

**성공 - 201 Created**

```json
{
  "id": 1,
  "record_id": 10,
  "is_new": true,
  "is_pneumonia": true,
  "confidence": 92.35,
  "heatmap_url": "data:image/png;base64,...",
  "model_name": "convnext_densenet_OR",
  "created_at": "2025-01-01T00:00:00"
}
```

**응답 필드**

| 필드명 | 타입 | 설명 |
|--------|------|------|
| id | integer | AI 분석 결과 고유 ID |
| record_id | integer | 연결된 진료기록 ID |
| is_new | boolean | 신규 분석 여부 (true: 새 분석, false: 재분석) |
| is_pneumonia | boolean | 폐렴 여부 (true: 폐렴, false: 정상) |
| confidence | float | 폐렴 클래스 확률 (0.00 ~ 100.00, 퍼센트) |
| heatmap_url | string | Grad-CAM 히트맵 이미지 (base64 인코딩 PNG) |
| model_name | string | 사용된 모델명 (`convnext_densenet_OR`) |
| created_at | string | 분석 일시 |

**실패**

- **400 Bad Request** - 이미지 파일 없음 또는 형식 오류
```json
{
  "detail": "유효하지 않은 이미지 파일입니다."
}
```

- **404 Not Found** - 진료기록 ID 없음
```json
{
  "detail": "해당 진료기록을 찾을 수 없습니다."
}
```

- **500 Internal Server Error** - 모델 로딩 실패
```json
{
  "detail": "AI 모델이 로드되지 않았습니다. 서버 관리자에게 문의하세요."
}
```

#### 비고
- **OR 앙상블**: ConvNeXt-Tiny, DenseNet121 두 모델 중 하나라도 폐렴(1)으로 판단하면 폐렴으로 결정
- **confidence**: 두 모델의 폐렴 클래스 확률 중 최댓값을 퍼센트로 반환 (0.00 ~ 100.00)
- **Grad-CAM**: 예측 확률이 더 높은 모델 기준으로 히트맵 생성
- **모델 파일**: 서버 시작 시 `app/worker/models/` 폴더에서 5-fold 가중치 자동 로드

---

### 3.2 예측 결과 단건 조회 — `GET /api/v1/ai/results/{result_id}`

#### 개요

| 항목 | 내용 |
|------|------|
| 설명 | 특정 AI 분석 결과를 ID로 조회하는 API |
| 메서드 | GET |
| 엔드포인트 | `/api/v1/ai/results/{result_id}` |
| 인증 필요 | Y |

#### 요청(Request)

**Headers**

| Key | Value | 설명 |
|-----|-------|------|
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| result_id | integer | ✅ | AI 분석 결과 고유 ID |

#### 응답(Response)

**성공 - 200 OK**

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 92.35,
  "heatmap_url": "data:image/png;base64,...",
  "model_name": "convnext_densenet_OR",
  "created_at": "2025-01-01T00:00:00"
}
```

**실패**

- **404 Not Found**
```json
{
  "detail": "해당 분석 결과를 찾을 수 없습니다."
}
```

---

### 3.3 예측 결과 목록 조회 — `GET /api/v1/ai/results`

#### 개요

| 항목 | 내용 |
|------|------|
| 설명 | AI 분석 결과 목록을 조회하는 API. record_id로 필터링 가능. |
| 메서드 | GET |
| 엔드포인트 | `/api/v1/ai/results` |
| 인증 필요 | Y |

#### 요청(Request)

**Headers**

| Key | Value | 설명 |
|-----|-------|------|
| Authorization | Bearer \<access_token\> | JWT 액세스 토큰 |

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| record_id | integer | ❌ | 특정 진료기록의 분석 결과만 조회 |

#### 응답(Response)

**성공 - 200 OK**

```json
[
  {
    "id": 1,
    "record_id": 10,
    "is_pneumonia": true,
    "confidence": 92.35,
    "model_name": "convnext_densenet_OR",
    "created_at": "2025-01-01T00:00:00"
  },
  {
    "id": 2,
    "record_id": 11,
    "is_pneumonia": false,
    "confidence": 12.50,
    "model_name": "convnext_densenet_OR",
    "created_at": "2025-01-02T00:00:00"
  }
]
```

> ※ 목록 조회에서는 `heatmap_url` 필드 제외 (용량 최적화)

---

## 4. 모델 정보

| 항목 | 내용 |
|------|------|
| 모델명 | `convnext_densenet_OR` |
| 앙상블 방식 | OR 앙상블 (두 모델 중 하나라도 폐렴이면 폐렴 판정) |
| 구성 모델 | ConvNeXt-Tiny (5-fold) + DenseNet121 (5-fold) |
| 입력 크기 | 224 × 224 px (RGB) |
| 출력 클래스 | 0: 정상, 1: 폐렴 |
| 시각화 | Grad-CAM 히트맵 (병변 위치 표시) |
| 가중치 경로 | `app/worker/models/` |

**가중치 파일 목록**

| 파일명 | 모델 |
|--------|------|
| `convnext_tiny_solo_fold1.pth` ~ `fold5.pth` | ConvNeXt-Tiny (5개) |
| `densenet121_fold1.pth` ~ `fold5.pth` | DenseNet121 (5개) |

---

## 5. 공통 에러 응답

| HTTP 상태 코드 | 설명 |
|--------------|------|
| 400 Bad Request | 잘못된 요청 (이미지 형식 오류 등) |
| 401 Unauthorized | 인증 실패 (토큰 없음 또는 만료) |
| 404 Not Found | 리소스를 찾을 수 없음 |
| 422 Unprocessable Entity | 입력값 검증 실패 |
| 500 Internal Server Error | 서버 내부 오류 (모델 로딩 실패 등) |