# 6일차 - AI 폐렴 예측 API 설계 명세서

> 본 문서는 `app/worker/model.py`의 `predict_pneumonia()` 함수(ConvNeXt-Tiny + DenseNet121 OR 앙상블 + Grad-CAM)와
> 사용자 요구사항 정의서(REQ-PRED-001/002)를 기준으로 작성한 API 명세입니다.

---

## 1. 개요 & 공통 규칙

- **Base URL**: `/api/v1`
- **인증**: 로그인된 사용자(사내 의료인·개발팀·연구자)만 호출 가능. (JWT 추후 적용, 현재는 기존 API와 동일 패턴)
- **데이터 형식**: 요청·응답 모두 JSON.
- **X-Ray 소스 (REQ-PRED-001)**: 예측에 쓰는 X-Ray는 **진료기록 저장 시 업로드된 이미지를 재사용**합니다. 예측 요청 시 **이미지를 새로 업로드하지 않습니다.** 진료기록에 X-Ray가 여러 장이면 **대표 1장**으로 예측합니다.
- **캐싱 (REQ-PRED-001)**: 같은 진료기록(`record_id`) + 같은 모델(`ai_model`) 결과가 이미 저장돼 있으면, **재추론 없이 저장된 데이터를 반환**합니다.
- **공통 상태 코드**
  - `201 Created` 신규 분석 수행 / `200 OK` 캐시 반환·목록 조회
  - `404 Not Found` 진료기록/X-Ray 없음 / `422 Unprocessable Entity` 입력값 오류
  - `500 Internal Server Error` 서버 내부 오류 (모델 미로드 등)
- **성능 (NFR-PRED-002)**: 모든 API 3초 이내 응답. 재호출은 캐싱으로, 첫 추론은 비동기 처리(threadpool)로 블로킹 회피.

---

## 2. 엔드포인트 요약

| No | 기능 | 메서드 | 엔드포인트 | 요구사항 |
|---|---|---|---|---|
| 1 | AI 폐렴 예측 (또는 캐시 반환) | POST | `/api/v1/medical-records/{record_id}/ai-analysis` | REQ-PRED-001 |
| 2 | 예측 결과 목록 조회 | GET | `/api/v1/medical-records/{record_id}/ai-analysis` | REQ-PRED-002 |

> 단건 조회 엔드포인트는 요구사항(REQ-PRED)에 없어 제외했습니다.

---

## 3. AI 폐렴 예측 API

### 3.1 AI 폐렴 예측 — `POST /api/v1/medical-records/{record_id}/ai-analysis` (REQ-PRED-001)

#### 개요

| 항목 | 내용 |
|------|------|
| 설명 | 진료기록의 **대표 X-Ray**로 폐렴 여부를 예측. 같은 (진료기록, 모델) 결과가 이미 있으면 **재추론 없이 저장값 반환**(캐싱). |
| 메서드 | POST |
| 엔드포인트 | `/api/v1/medical-records/{record_id}/ai-analysis` |
| 인증 필요 | Y |

#### 요청(Request)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| record_id | integer | ✅ | 진료기록 ID (medical_records.id) |

**Request Body**: 없음 — X-Ray는 진료기록에 저장된 이미지를 사용합니다.

#### 응답(Response)

응답 본문 형태는 동일하며, **신규 분석인지 캐시 반환인지에 따라 상태 코드가 다릅니다.**

| 상황 | 상태 코드 | `is_new` |
|------|----------|---------|
| 신규 분석 수행 | **201 Created** | `true` |
| 기존 저장값 반환(캐시 히트) | **200 OK** | `false` |

```json
{
  "id": 1,
  "record_id": 10,
  "is_new": true,
  "is_pneumonia": true,
  "confidence": 92.35,
  "heatmap_url": "data:image/png;base64,...",
  "ai_model": "convnext_densenet_OR",
  "created_at": "2026-01-01T00:00:00"
}
```

**응답 필드**

| 필드명 | 타입 | 설명 |
|--------|------|------|
| id | integer | AI 분석 결과 고유 ID |
| record_id | integer | 연결된 진료기록 ID |
| is_new | boolean | 신규 분석 여부 (`true`: 새 분석, `false`: 캐시 반환) |
| is_pneumonia | boolean | 폐렴 여부 (`true`: 폐렴, `false`: 정상) |
| confidence | float | 폐렴 클래스 확률 (0.00 ~ 100.00, **퍼센트**) |
| heatmap_url | string \| null | Grad-CAM 히트맵 (base64 data URI). **선택사항** — 실패 시 `null` |
| ai_model | string | 사용된 모델명 (`convnext_densenet_OR`) |
| created_at | string | 분석 일시 |

**실패**

- **404 Not Found** — 진료기록 없음
```json
{ "detail": "해당 진료기록을 찾을 수 없습니다." }
```
- **404 Not Found** — 진료기록에 X-Ray 이미지가 없음
```json
{ "detail": "예측할 X-Ray 이미지가 없습니다." }
```
- **500 Internal Server Error** — 모델 미로드
```json
{ "detail": "AI 모델이 로드되지 않았습니다. 서버 관리자에게 문의하세요." }
```

#### 비고
- **캐싱**: 동일 `(record_id, ai_model)` 결과가 있으면 추론을 생략하고 저장값을 200으로 반환합니다(REQ-PRED-001).
- **히트맵은 선택사항**: Grad-CAM 실패 시 `heatmap_url=null`이며, 예측 결과(`is_pneumonia`, `confidence`)는 정상 반환됩니다. (DB: `heatmap_url = Text, nullable`)
- **confidence**: 두 모델의 폐렴 클래스 확률 중 최댓값을 **퍼센트(0~100)** 로 반환 (모델 내부에서 변환 완료).
- **OR 앙상블**: ConvNeXt-Tiny, DenseNet121 중 하나라도 폐렴(1)이면 폐렴으로 판정.
- **대표 X-Ray**: 진료기록에 X-Ray가 여러 장이면 대표 1장으로만 예측.

---

### 3.2 예측 결과 목록 조회 — `GET /api/v1/medical-records/{record_id}/ai-analysis` (REQ-PRED-002)

#### 개요

| 항목 | 내용 |
|------|------|
| 설명 | 해당 진료기록의 AI 예측 결과를 목록으로 조회 |
| 메서드 | GET |
| 엔드포인트 | `/api/v1/medical-records/{record_id}/ai-analysis` |
| 인증 필요 | Y |

#### 요청(Request)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| record_id | integer | ✅ | 진료기록 ID |

#### 응답(Response)

**성공 - 200 OK**

```json
[
  {
    "id": 1,
    "record_id": 10,
    "is_pneumonia": true,
    "confidence": 92.35,
    "ai_model": "convnext_densenet_OR",
    "created_at": "2026-01-01T00:00:00"
  }
]
```

**목록 응답 필드** — `id`, `record_id`, `is_pneumonia`, `confidence`, `ai_model`, `created_at`

> ※ 목록 조회에서는 **`heatmap_url` 제외** (base64라 용량이 커서). 히트맵은 예측(3.1) 응답에만 포함됩니다.

**실패**

- **404 Not Found** — 진료기록 없음
```json
{ "detail": "해당 진료기록을 찾을 수 없습니다." }
```

---

## 4. 모델 정보

| 항목 | 내용 |
|------|------|
| 모델명(ai_model) | `convnext_densenet_OR` |
| 앙상블 방식 | OR 앙상블 (두 모델 중 하나라도 폐렴이면 폐렴 판정) |
| 구성 모델 | ConvNeXt-Tiny (5-fold) + DenseNet121 (5-fold) |
| 입력 크기 | 224 × 224 px (RGB) |
| 출력 클래스 | 0: 정상, 1: 폐렴 |
| 시각화 | Grad-CAM 히트맵 (병변 위치 표시, 실패 시 생략) |
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
| 404 Not Found | 진료기록·X-Ray 등 리소스를 찾을 수 없음 |
| 422 Unprocessable Entity | 입력값 검증 실패 (예: `record_id`가 정수가 아님) |
| 500 Internal Server Error | 서버 내부 오류 (모델 미로드 등) |

---

## 6. 데이터 모델 (참고 — ai_analysis_results)

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | bigint PK | 고유 ID |
| record_id | bigint FK → medical_records | 진료기록 (CASCADE) |
| is_pneumonia | boolean | 폐렴 여부 |
| confidence | numeric(5,2) | 0.00~100.00 (퍼센트) |
| heatmap_url | **Text, nullable** | base64 data URI / 실패 시 NULL |
| ai_model | varchar(50) | 사용 모델명 |
| created_at | datetime | 분석 일시 |

> `is_new`는 DB에 저장하지 않는 **응답 전용 필드**입니다 (신규/캐시 구분용).
