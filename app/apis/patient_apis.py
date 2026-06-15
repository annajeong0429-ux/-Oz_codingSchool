# app/apis/patient_apis.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.patient_schemas import PatientCreate, PatientUpdate, PatientResponse
from app.services import patient_services as service
from app.models.enums import GenderEnum

# prefix로 공통 주소를 한 번에 → 각 경로가 짧아짐
router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


# 환자 등록 (REQ-PTNT-001) → 201
@router.post(
    "",
    summary="환자 정보 등록",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient_handler(
    data: PatientCreate,
    db: AsyncSession = Depends(async_get_db),   # DB 세션을 주입받음
):
    return await service.register_patient(db, data)


# 환자 목록 조회 (REQ-PTNT-002) → 200
@router.get("", summary="환자 목록 조회", response_model=list[PatientResponse])
async def list_patients_handler(
    name: str | None = None,
    gender: GenderEnum | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.list_patients(db, name, gender, age_min, age_max)


# 환자 상세 조회 (REQ-PTNT-003) → 200
@router.get("/{patient_id}", summary="환자 상세 조회", response_model=PatientResponse)
async def get_patient_handler(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.get_patient_or_404(db, patient_id)


# 환자 수정 (REQ-PTNT-004) → 200
@router.patch("/{patient_id}", summary="환자 정보 수정", response_model=PatientResponse)
async def update_patient_handler(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.modify_patient(db, patient_id, data)


# 환자 삭제 (REQ-PTNT-005) → 204 (본문 없음)
@router.delete("/{patient_id}", summary="환자 정보 삭제", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_handler(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
):
    await service.remove_patient(db, patient_id)
    # 204는 돌려줄 내용 없음 → 아무것도 return 안 함
