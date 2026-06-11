# app/apis/medical_record_apis.py
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.medical_record_schemas import MedicalRecordResponse, MedicalRecordListItem
from app.services import medical_record_services as service

router = APIRouter(prefix="/api/v1", tags=["medical-records"])


# 진료기록 등록 (REQ-MDR-001) — multipart 파일 업로드
@router.post(
    "/patients/{patient_id}/medical-records",
    summary="진료기록 등록 (X-ray 업로드)",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record_handler(
    patient_id: int,
    chart_number: str = Form(...),
    symptoms: str = Form(...),
    shooting_datetime: datetime = Form(...),
    xray_image: UploadFile = File(...),
    user_id: int | None = Form(None),          # JWT 전엔 선택 (작성 의사)
    db: AsyncSession = Depends(async_get_db),
):
    return await service.register_medical_record(
        db,
        patient_id=patient_id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_image=xray_image,
        shooting_datetime=shooting_datetime,
        user_id=user_id,
    )


# 진료기록 목록 (REQ-MDR-002)
@router.get(
    "/patients/{patient_id}/medical-records",
    summary="환자별 진료기록 목록",
    response_model=list[MedicalRecordListItem],
)
async def list_medical_records_handler(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.list_medical_records(db, patient_id)


# 진료기록 상세 (REQ-MDR-003)
@router.get(
    "/medical-records/{record_id}",
    summary="진료기록 상세 조회",
    response_model=MedicalRecordResponse,
)
async def get_medical_record_handler(
    record_id: int,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.get_medical_record(db, record_id)
