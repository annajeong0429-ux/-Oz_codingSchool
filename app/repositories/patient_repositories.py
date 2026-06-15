# app/repositories/patient_repositories.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient_schemas import PatientCreate, PatientUpdate


# 등록 (REQ-PTNT-001)
async def create_patient(db: AsyncSession, data: PatientCreate) -> Patient:
    patient = Patient(**data.model_dump())   # 스키마(검증된 입력) → 모델 객체로 변환
    db.add(patient)                          # 세션에 "추가할게" 등록
    await db.commit()                        # 실제 DB에 저장(INSERT)
    await db.refresh(patient)                # DB가 채워준 id·created_at을 다시 읽어옴
    return patient


# 단건 조회 (id로) — 상세조회/수정/삭제에서 공용
async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()       # 있으면 객체, 없으면 None


# 목록 조회 + 검색·필터 (REQ-PTNT-002)
async def get_patients(
    db: AsyncSession,
    name: str | None = None,
    gender: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
) -> list[Patient]:
    query = select(Patient)
    if name is not None:
        query = query.where(Patient.name.contains(name))   # 이름 부분 검색
    if gender is not None:
        query = query.where(Patient.gender == gender)
    if age_min is not None:
        query = query.where(Patient.age >= age_min)
    if age_max is not None:
        query = query.where(Patient.age <= age_max)
    result = await db.execute(query)
    return list(result.scalars().all())


# 수정 (REQ-PTNT-004) — 입력된 항목만 반영
async def update_patient(db: AsyncSession, patient: Patient, data: PatientUpdate) -> Patient:
    update_data = data.model_dump(exclude_unset=True)   # 보낸 항목만 추림
    for field, value in update_data.items():
        setattr(patient, field, value)                  # 그 항목만 덮어쓰기
    await db.commit()
    await db.refresh(patient)
    return patient


# 삭제 (REQ-PTNT-005)
async def delete_patient(db: AsyncSession, patient: Patient) -> None:
    await db.delete(patient)
    await db.commit()
