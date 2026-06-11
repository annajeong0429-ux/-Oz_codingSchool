# app/schemas/medical_record_schemas.py
from datetime import datetime
from pydantic import BaseModel


# 등록·상세 응답 (REQ-MDR-001 / 003)
class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_image_url: str | None      # 접근 가능한 경로 (예: /media/xray/abc.png)
    created_at: datetime


# 목록 응답 (REQ-MDR-002) — symptoms는 100자 초과 시 "..." 생략
class MedicalRecordListItem(BaseModel):
    id: int
    chart_number: str
    symptoms: str                   # 목록에선 100자까지만 (서비스에서 자름)
    created_at: datetime
