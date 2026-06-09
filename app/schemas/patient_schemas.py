# app/schemas/patient_schemas.py
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import GenderEnum   # 모델과 같은 성별 enum 재사용


# 입력: 환자 등록 (REQ-PTNT-001) — 이름·나이·성별·연락처 필수
class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    age: int = Field(ge=0, le=150)
    gender: GenderEnum                      # "male" / "female"만 허용
    phone: str = Field(max_length=11)


# 입력: 환자 수정 (REQ-PTNT-004) — 이름·연락처만, 부분 수정(둘 다 선택)
class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = Field(default=None, max_length=11)


# 출력: 환자 응답 (목록·상세 조회 공용)
class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: GenderEnum
    phone: str
    created_at: datetime
    updated_at: datetime | None

    # SQLAlchemy 모델 객체를 이 틀로 자동 변환 허용 (DB → 응답)
    model_config = {"from_attributes": True}
