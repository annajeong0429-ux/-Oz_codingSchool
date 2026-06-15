# AI Health Web — 흉부 X-Ray 폐렴 판독 백오피스

흉부 X-Ray 이미지를 업로드하면 AI(ConvNeXt + DenseNet 앙상블)가 폐렴 여부를 예측하고,
의료진이 환자·진료기록을 관리할 수 있는 백오피스 웹 서비스입니다.

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Auth | JWT (python-jose, bcrypt) |
| Database | MySQL 8.0 |
| Cache / Queue | Redis 7 (List 큐 + Pub/Sub) |
| AI 모델 | ConvNeXt-Tiny + DenseNet121 OR 앙상블 (PyTorch) |
| Container | Docker, Docker Compose |
| Frontend | Vanilla JS SPA |

---

## 프로젝트 구조

```
.
├── app/
│   ├── apis/           # 엔드포인트 (user, patient, medical_record, ai_analysis)
│   ├── core/           # 설정, DB, Redis 클라이언트, JWT 인증
│   ├── models/         # SQLAlchemy ORM 모델
│   ├── repositories/   # DB 쿼리
│   ├── schemas/        # Pydantic 스키마
│   ├── services/       # 비즈니스 로직
│   └── worker/
│       ├── model.py    # AI 추론 함수 (predict_pneumonia)
│       └── models/     # 가중치 파일 (.pth) ← Git 미포함, 별도 다운로드
├── worker/             # AI 추론 워커 (소비자 컨테이너)
│   ├── main.py         # BRPOP → 추론 → PUBLISH 루프
│   ├── redis_client.py # sync Redis 클라이언트
│   └── Dockerfile
├── static/             # 프론트엔드 SPA
├── alembic/            # DB 마이그레이션
├── docker-compose.yml
└── .env                # 환경변수 (Git 미포함)
```

---

## 환경변수 설정 (.env)

프로젝트 루트에 `.env` 파일을 생성하세요.

`.env.example`을 복사해서 값을 채워주세요.

```bash
cp .env.example .env
```

```env
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ai_health
DB_HOST=localhost
DB_PORT=3306

JWT_SECRET_KEY=your-secret-key-here

REDIS_URL=redis://localhost:6379/0
```

> Docker Compose로 실행할 경우 `DB_HOST=mysql`, `REDIS_URL=redis://redis:6379/0` 으로 자동 주입됩니다.

---

## 실행 방법

### Docker Compose (권장)

```bash
# 1. 환경변수 파일 생성
cp .env.example .env   # 값 수정 필요

# 2. AI 모델 가중치 다운로드 후 app/worker/models/ 에 저장 (하단 참고)

# 3. 전체 실행 (fastapi + mysql + redis + ai-worker)
docker compose up --build

# 4. DB 마이그레이션
docker compose exec fastapi alembic upgrade head

# 5. 브라우저 접속
# http://localhost:8000
```

### 로컬 실행

```bash
# 1. 의존성 설치
uv sync

# 2. MySQL, Redis 별도 실행 필요

# 3. DB 마이그레이션
uv run alembic upgrade head

# 4. FastAPI 서버 실행
fastapi run app/main.py

# 5. AI 워커 실행 (별도 터미널)
python worker/main.py
```

---

## 프로젝트 진행 과정

Team Rule 수립부터 AI 워커 비동기 아키텍처 설계까지 단계별 학습·구현 내용을 정리합니다.

| 일차 | 주제 | 문서 |
|------|------|------|
| 1일차 | 팀 규칙 수립 (코어타임, Git 브랜치 전략, 커밋 컨벤션) | [docs/1일차_우당탕탕team_rules.md](docs/1일차_우당탕탕team_rules.md) |
| 2일차 | Git Flow / GitHub Flow 비교 및 팀 하이브리드 브랜치 전략 확정 | [docs/2일차_git_branch_전략_최종 (1).md](<docs/2일차_git_branch_전략_최종 (1).md>) |
| 3일차 | 프로젝트 구조 분석 (FastAPI, SQLAlchemy, Alembic, Docker) | [docs/3일차_프로젝트_뜯어보기.md](docs/3일차_프로젝트_뜯어보기.md) |
| 4일차 | User API 설계 (회원가입/로그인/JWT/관리자 권한) | [docs/4일차_USER_API_설계.md](docs/4일차_USER_API_설계.md) |
| 5일차 | 환자·진료기록 API 설계 (CRUD, X-Ray 업로드) | [docs/5일차_환자관리_API_설계.md](docs/5일차_환자관리_API_설계.md) |
| 6일차 | AI 폐렴 예측 API 설계 (캐싱, run_in_threadpool 한계 분석) | [docs/6일차_AI_폐렴예측_API설계.md](docs/6일차_AI_폐렴예측_API설계.md) |
| 7일차 | 프론트엔드 API 연결 및 앱 실행화면 | [docs/7일차_앱_실행화면.md](docs/7일차_앱_실행화면.md) |
| 8일차 | Docker 컨테이너화 (Dockerfile, docker-compose, Redis 통합) | 이미지 캡처: [docs/images/](docs/images/) |
| 9일차 | 동시성 문제 해결 — Redis 작업 큐 + AI 워커 분리 아키텍처 설계 | [docs/9일차_동시성문제_해결을위한_아키텍처설계.md](docs/9일차_동시성문제_해결을위한_아키텍처설계.md) |
| QA | Swagger UI 수동 테스트 (201 신규·200 캐시·404·422) + Docker e2e 예측 흐름 검증 | [docs/images/](docs/images/) |
| AWS 배포 | _(미진행)_ | — |

---

## API 엔드포인트

### 인증 (Auth / Users)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/users/signup` | 회원가입 |
| POST | `/api/v1/users/login` | 로그인 (FormData) |
| POST | `/api/v1/users/logout` | 로그아웃 |
| POST | `/api/v1/users/refresh` | 토큰 갱신 |
| GET | `/api/v1/users/me` | 내 정보 조회 |
| PATCH | `/api/v1/users/me` | 내 정보 수정 |
| PATCH | `/api/v1/users/me/password` | 비밀번호 변경 |
| DELETE | `/api/v1/users/me` | 회원 탈퇴 |

### 관리자
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/admin/users` | 전체 유저 목록 |
| PATCH | `/api/v1/admin/users/role` | 유저 권한 변경 |

### 환자 (Patient)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/patients` | 환자 등록 |
| GET | `/api/v1/patients` | 환자 목록 조회 (검색/필터) |
| GET | `/api/v1/patients/{id}` | 환자 상세 조회 |
| PATCH | `/api/v1/patients/{id}` | 환자 정보 수정 |
| DELETE | `/api/v1/patients/{id}` | 환자 삭제 |

### 진료기록 (Medical Record)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/medical-records` | 진료기록 등록 (X-Ray 업로드 포함) |
| GET | `/api/v1/patients/{id}/medical-records` | 환자별 진료기록 목록 |
| GET | `/api/v1/medical-records/{id}` | 진료기록 상세 |

### AI 폐렴 예측
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/medical-records/{id}/ai-analysis` | AI 예측 요청 (캐시 없으면 워커에 위임) |
| GET | `/api/v1/medical-records/{id}/ai-analysis` | 예측 결과 목록 조회 |

> Swagger UI: `http://localhost:8000/docs`

---

## DB 마이그레이션

```bash
# 마이그레이션 파일 자동 생성
uv run alembic revision --autogenerate -m "변경 내용 설명"

# DB에 반영
uv run alembic upgrade head

# 롤백
uv run alembic downgrade -1
```

---

## AI 모델 가중치 설정

가중치 파일은 용량 문제로 Git에 포함되지 않습니다.
아래 Google Drive에서 다운로드 후 `app/worker/models/` 폴더에 저장하세요.

**다운로드:** https://drive.google.com/drive/folders/1x8TnELyNyFajk-VBzJw8z21yUm1EDKDR?usp=sharing

| 파일명 | 모델 |
|--------|------|
| `convnext_tiny_solo_fold1.pth` ~ `fold5.pth` | ConvNeXt-Tiny (5-Fold) |
| `densenet121_fold1.pth` ~ `fold5.pth` | DenseNet121 (5-Fold) |

```
app/worker/models/
├── convnext_tiny_solo_fold1.pth
├── ...
├── densenet121_fold1.pth
└── densenet121_fold5.pth
```
