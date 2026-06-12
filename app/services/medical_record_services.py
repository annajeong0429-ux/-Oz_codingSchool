# app/services/medical_record_services.py
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.medical_record_schemas import MedicalRecordResponse, MedicalRecordListItem
from app.repositories import medical_record_repositories as repo
from app.repositories import patient_repositories as patient_repo   # 환자 존재 확인 재사용

# 프로젝트 루트/media/xray  (app/services/ → 3단계 위가 루트)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
XRAY_DIR = BASE_DIR / "media" / "xray"


# 진료기록 등록 (REQ-MDR-001)
async def register_medical_record(
    db: AsyncSession,
    patient_id: int,
    chart_number: str,
    symptoms: str,
    xray_image: UploadFile,
    shooting_datetime: datetime,
    user_id: int | None = None,
) -> MedicalRecordResponse:
    # 1. 환자 존재 확인 (없으면 404) — patient repo 재사용
    if await patient_repo.get_patient_by_id(db, patient_id) is None:
        raise HTTPException(status_code=404, detail="해당 환자를 찾을 수 없습니다.")

    # 2. X-ray 파일을 서버 로컬(media/xray/)에 저장
    XRAY_DIR.mkdir(parents=True, exist_ok=True)              # 폴더 없으면 생성
    ext = Path(xray_image.filename).suffix or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"                    # 충돌 방지 고유 이름
    content = await xray_image.read()
    with open(XRAY_DIR / filename, "wb") as f:
        f.write(content)
    image_url = f"media/xray/{filename}"                     # 상대경로 저장 (AI open + URL 유도)

    # 3. 진료기록 생성 → 4. X-ray 행 생성 (record.id로 연결)
    record = await repo.create_medical_record(
        db, patient_id=patient_id, user_id=user_id,
        chart_number=chart_number, symptoms=symptoms,
    )
    await repo.create_xray_image(
        db, record_id=record.id, uploader_id=user_id,
        image_url=image_url, shooting_datetime=shooting_datetime,
    )

    # 5. 응답 조립 (xray_image_url = 프론트 접근용 URL)
    return MedicalRecordResponse(
        id=record.id, patient_id=record.patient_id,
        chart_number=record.chart_number, symptoms=record.symptoms,
        xray_image_url=f"/{image_url}",                      # /media/xray/...
        created_at=record.created_at,
    )


# 진료기록 목록 (REQ-MDR-002) — symptoms 100자 초과 시 "..."
async def list_medical_records(db: AsyncSession, patient_id: int) -> list[MedicalRecordListItem]:
    if await patient_repo.get_patient_by_id(db, patient_id) is None:
        raise HTTPException(status_code=404, detail="해당 환자를 찾을 수 없습니다.")
    records = await repo.list_records_by_patient(db, patient_id)
    return [
        MedicalRecordListItem(
            id=r.id,
            chart_number=r.chart_number,
            symptoms=(r.symptoms[:100] + "...") if len(r.symptoms) > 100 else r.symptoms,
            created_at=r.created_at,
        )
        for r in records
    ]


# 진료기록 상세 (REQ-MDR-003)
async def get_medical_record(db: AsyncSession, record_id: int) -> MedicalRecordResponse:
    record = await repo.get_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="해당 진료기록을 찾을 수 없습니다.")
    xray = await repo.get_xray_by_record(db, record_id)      # 대표 X-ray
    return MedicalRecordResponse(
        id=record.id, patient_id=record.patient_id,
        chart_number=record.chart_number, symptoms=record.symptoms,
        xray_image_url=(f"/{xray.image_url}" if xray else None),
        created_at=record.created_at,
    )
