# app/repositories/medical_record_repositories.py
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage


# 진료기록 생성
async def create_medical_record(
    db: AsyncSession,
    patient_id: int,
    user_id: int | None,
    chart_number: str,
    symptoms: str,
) -> MedicalRecord:
    record = MedicalRecord(
        patient_id=patient_id,
        user_id=user_id,        # JWT 없어 None 가능 (nullable)
        chart_number=chart_number,
        symptoms=symptoms,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)    # 생성된 id 받아옴 (X-ray가 참조)
    return record


# X-ray 이미지 생성 (진료기록에 연결)
async def create_xray_image(
    db: AsyncSession,
    record_id: int,
    uploader_id: int | None,
    image_url: str,
    shooting_datetime: datetime,
) -> XrayImage:
    xray = XrayImage(
        record_id=record_id,
        uploader_id=uploader_id,    # None 가능 (nullable)
        image_url=image_url,
        shooting_datetime=shooting_datetime,
    )
    db.add(xray)
    await db.commit()
    await db.refresh(xray)
    return xray


# 진료기록 단건 조회 (id로)
async def get_record_by_id(db: AsyncSession, record_id: int) -> MedicalRecord | None:
    result = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    return result.scalar_one_or_none()


# 환자별 진료기록 목록 (REQ-MDR-002)
async def list_records_by_patient(db: AsyncSession, patient_id: int) -> list[MedicalRecord]:
    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.created_at.desc())   # 최신순 (리뷰 반영)
    )
    return list(result.scalars().all())


# 진료기록의 대표 X-ray 1장 (상세 응답에서 image_url 가져올 때)
async def get_xray_by_record(db: AsyncSession, record_id: int) -> XrayImage | None:
    result = await db.execute(
        select(XrayImage)
        .where(XrayImage.record_id == record_id)
        .order_by(XrayImage.id)
        .limit(1)
    )
    return result.scalars().first()
