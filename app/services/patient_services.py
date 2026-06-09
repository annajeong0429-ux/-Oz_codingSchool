# app/services/patient_services.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient_schemas import PatientCreate, PatientUpdate
from app.repositories import patient_repositories as repo   # repository를 repo로 줄여 사용


# 등록
async def register_patient(db: AsyncSession, data: PatientCreate) -> Patient:
    return await repo.create_patient(db, data)


# 단건 조회 (없으면 404) — 상세/수정/삭제가 공통으로 재사용
async def get_patient_or_404(db: AsyncSession, patient_id: int) -> Patient:
    patient = await repo.get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")
    return patient


# 목록 조회 (검색·필터)
async def list_patients(
    db: AsyncSession,
    name: str | None = None,
    gender: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
) -> list[Patient]:
    return await repo.get_patients(db, name, gender, age_min, age_max)


# 수정 (REQ-PTNT-004)
async def modify_patient(db: AsyncSession, patient_id: int, data: PatientUpdate) -> Patient:
    # 수정할 항목이 하나도 없으면 400
    if data.name is None and data.phone is None:
        raise HTTPException(status_code=400, detail="최소 하나의 항목을 입력해야 합니다.")
    patient = await get_patient_or_404(db, patient_id)
    return await repo.update_patient(db, patient, data)

# 삭제 (REQ-PTNT-005)
async def remove_patient(db: AsyncSession, patient_id: int) -> None:
    patient = await get_patient_or_404(db, patient_id)   # 먼저 존재 확인(없으면 404)
    await repo.delete_patient(db, patient)
