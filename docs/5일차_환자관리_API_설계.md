# 5일차 - 환자 관리 및 진료기록 API 설계

> 본 문서는 **5일차 진료기록 사용자 요구사항 정의서**(REQ-PTNT-001~005, REQ-MDR-001~003, NFR)를 기준으로 작성한 API 명세입니다.
> 필드명·엔드포인트는 3일차에 작성한 SQLAlchemy 모델(ERD)과 일치시켜 최종 확인합니다.

---

## 1. 개요 & 공통 규칙

- **Base URL**: `/api/v1` (템플릿 `main.py`의 catch-all이 `api/v1`을 API 경로로 취급하므로 그 아래로 라우트됩니다.)
- **인증**: 로그인된 사용자(사내 개발진·의료 실무진·연구진)만 호출 가능. 로그인 토큰은 **Stage 4 User API에 의존**합니다.
- **데이터 형식**: 기본 JSON. 단, 진료기록 등록(X-Ray 업로드)은 `multipart/form-data`.
- **공통 상태 코드**
  - `200 OK` 조회·수정 성공 / `201 Created` 등록 성공 / `204 No Content` 삭제 성공
  - `404 Not Found` 존재하지 않는 ID / `422 Unprocessable Entity` 입력값 검증 실패
- **성능(NFR-PTNT-001, NFR-MDR-001)**: 모든 API는 **최대 3초 이내** 처리·응답.

---

## 2. 엔드포인트 요약

| 요구사항 ID | 기능 | 메서드 | 엔드포인트 |
|---|---|---|---|
| REQ-PTNT-001 | 환자 정보 등록 | POST | `/api/v1/patients` |
| REQ-PTNT-002 | 환자 목록 조회 | GET | `/api/v1/patients` |
| REQ-PTNT-003 | 환자 상세 조회 | GET | `/api/v1/patients/{patient_id}` |
| REQ-PTNT-004 | 환자 정보 수정 | PATCH | `/api/v1/patients/{patient_id}` |
| REQ-PTNT-005 | 환자 정보 삭제 | DELETE | `/api/v1/patients/{patient_id}` |
| REQ-MDR-001 | 진료기록 등록 | POST | `/api/v1/patients/{patient_id}/medical-records` |
| REQ-MDR-002 | 진료기록 목록 조회 | GET | `/api/v1/patients/{patient_id}/medical-records` |
| REQ-MDR-003 | 진료기록 상세 조회 | GET | `/api/v1/medical-records/{record_id}` |

---

## 3. 환자 관리 API (Patients)

> 데이터 모델: `patients(id, name, age, gender, phone, created_at, updated_at)`

### 3.1 환자 정보 등록 — `POST /api/v1/patients` (REQ-PTNT-001)
- **설명**: 사내 의료인이 환자 정보를 등록.
- **Request Body** (application/json)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| name | string | ✅ | 이름 |
| age | integer | ✅ | 나이 |
| gender | string(enum) | ✅ | 성별 (`male`/`female`) |
| phone | string | ✅ | 연락처(휴대폰 번호) |

- **Response `201`**: `{ id, name, age, gender, phone, created_at, updated_at }`
- **검증**: 4개 항목 필수, 휴대폰 번호 형식, 나이 범위. 실패 시 `422`.

### 3.2 환자 목록 조회 — `GET /api/v1/patients` (REQ-PTNT-002)
- **설명**: 등록된 환자 목록 조회. 이름 검색 + 성별·나이범위 필터 제공.
- **Query Parameters** (모두 선택)

| 파라미터 | 타입 | 설명 |
|---|---|---|
| name | string | 이름 기준 검색 |
| gender | string | 성별 필터 |
| age_min | integer | 나이 하한 |
| age_max | integer | 나이 상한 |

- **Response `200`**: 배열, 항목별 필드 → `id`, `name`, `age`, `gender`, `phone`, `created_at`, `updated_at`

### 3.3 환자 상세 조회 — `GET /api/v1/patients/{patient_id}` (REQ-PTNT-003)
- **Path**: `patient_id` (정수)
- **Response `200`**: `{ id, name, gender, phone, age }` (확인 항목: 이름·성별·연락처·나이 + 식별용 id)
- **에러**: 없는 id → `404`

### 3.4 환자 정보 수정 — `PATCH /api/v1/patients/{patient_id}` (REQ-PTNT-004)
- **설명**: 부분 수정(입력된 항목만 반영).
- **Request Body** (부분 수정) — 요구사항 정의서 기준 **수정 가능 항목은 이름·연락처**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| name | string | ❌ | 이름 |
| phone | string | ❌ | 연락처 |

- **Response `200`**: 수정된 환자 정보 / 없는 id → `404`

### 3.5 환자 정보 삭제 — `DELETE /api/v1/patients/{patient_id}` (REQ-PTNT-005)
- **설명**: 환자 삭제. **해당 환자의 진료기록과 X-Ray 이미지도 함께 영구 삭제(cascade)**.
- **Response `204`** / 없는 id → `404`
- **비고**: "관련 데이터가 모두 삭제됨" 안내 팝업·확인 절차는 프론트 UX이고, API는 확인 이후 삭제를 수행. 연관 진료기록·X-Ray 이미지(레코드 + 로컬 이미지 파일) 삭제 처리 필요.

---

## 4. 진료기록 API (Medical Records)

> 데이터 모델: `medical_records(id, patient_id FK, chart_number, symptoms, created_at, updated_at)`
> X-Ray 이미지는 **별도 테이블** `xray_images(id, record_id FK, uploader_id FK, image_url, shooting_datetime, created_at)` 에 저장됩니다.
> → 진료기록 등록 1건은 **medical_records 1행 + xray_images 1행을 함께 생성**합니다.

### 4.1 진료기록 등록 — `POST /api/v1/patients/{patient_id}/medical-records` (REQ-MDR-001)
- **설명**: 선택한 환자의 X-Ray 사진을 포함한 진료기록을 등록.
- **Content-Type**: `multipart/form-data` (이미지 파일 업로드)
- **Path**: `patient_id` (환자 고유 ID)
- **Form Fields**

| 필드 | 타입 | 필수 | 저장 위치 | 설명 |
|---|---|---|---|---|
| chart_number | string | ✅ | medical_records | 진료 차트 넘버 |
| symptoms | string | ✅ | medical_records | 진료된 증상 |
| xray_image | file | ✅ | (파일→로컬) image_url | 촬영된 흉부 X-Ray 이미지 |
| shooting_datetime | datetime | ✅ | xray_images | X-Ray 촬영 일시 |

- **업로더(uploader_id)**: 로그인된 사용자(의사) ID를 서버에서 xray_images에 기록.
- **이미지 저장**: 파일은 **서버 실행 환경의 로컬 저장소**에 저장하고, 그 경로를 `xray_images.image_url`에 기록. (업로드 미리보기는 프론트 처리)
- **Response `201`**:
  ```json
  {
    "id": 1, "patient_id": 1, "chart_number": "C-001", "symptoms": "기침, 발열",
    "created_at": "...",
    "xray_image": { "id": 1, "image_url": ".../xray/1.png", "shooting_datetime": "..." }
  }
  ```

### 4.2 진료기록 목록 조회 — `GET /api/v1/patients/{patient_id}/medical-records` (REQ-MDR-002)
- **설명**: 해당 환자의 진료기록 목록 조회.
- **Response `200`**: 배열, 항목별 필드 → `record_id`(=id), `chart_number`, `symptoms`(**100자 초과 시 `...` 생략 형태**), `created_at`
- **참고**: 요구사항 정의서에 이 항목 구분이 "비기능"으로 표기돼 있으나, 실제로는 조회(기능)에 해당합니다. → **확인 필요**

### 4.3 진료기록 상세 조회 — `GET /api/v1/medical-records/{record_id}` (REQ-MDR-003)
- **Path**: `record_id`
- **Response `200`**: `{ record_id, chart_number, symptoms, xray_image_url, created_at }`
  - `xray_image_url` = 연결된 `xray_images.image_url` (접근 가능한 경로/URL)
- **에러**: 없는 id → `404`

### 4.4 진료기록 수정 / 삭제 — **확인 필요**
> 과제 안내문에는 진료기록을 "등록·조회·**수정·삭제**"한다고 되어 있으나, **요구사항 정의서에는 REQ-MDR-001~003(등록·목록·상세)만** 정의되어 있고 수정·삭제 항목이 없습니다.
> → 진료기록 수정·삭제 API가 범위에 포함되는지 **확인 필요**. 포함 시 아래 안으로 추가.

| 기능 | 메서드 | 엔드포인트 |
|---|---|---|
| 진료기록 수정 | PATCH | `/api/v1/medical-records/{record_id}` |
| 진료기록 삭제 | DELETE | `/api/v1/medical-records/{record_id}` |

---

## 5. 데이터 모델 필드 요약 (3일차 모델과 대조용)

- **Patient**: `id`, `name`, `age`, `gender`, `phone`, `created_at`, `updated_at`
- **MedicalRecord**: `id`, `patient_id`(FK → Patient), `chart_number`, `symptoms`, `created_at`, `updated_at`
- **XrayImage**: `id`, `record_id`(FK → MedicalRecord), `uploader_id`(FK → User), `image_url`, `shooting_datetime`, `created_at`
- 환자 삭제 시 MedicalRecord·XrayImage(레코드 + 로컬 이미지 파일)가 함께 삭제되도록 cascade(또는 서비스 로직) 설계.

> 본 명세의 필드명은 3일차 ORM 모델의 컬럼명과 반드시 일치시켜야 합니다. (모델 PR 확정 후 최종 대조)

---

## 6. 작업 분배 제안 (3인)

"각 API 최소 1개" 조건에 맞춰, 자원(환자/진료기록)과 난이도를 섞어 나눕니다.

| 담당 | API |
|---|---|
| A | 환자 등록(3.1) + 환자 목록 조회(3.2) |
| B | 환자 상세(3.3) + 환자 수정(3.4) + 환자 삭제(3.5, cascade) |
| C | 진료기록 등록(4.1, 파일 업로드) + 진료기록 목록(4.2) + 진료기록 상세(4.3) |

> 진료기록 등록(파일 업로드)이 가장 까다로우므로 C가 그쪽에 집중. 공통 스키마(Pydantic)·모델을 먼저 한 명이 잡고 병합 후 분기하면 충돌이 줄어듭니다.
