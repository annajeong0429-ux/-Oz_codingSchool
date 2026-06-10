# app/schemas/ai_analysis_schemas.py
from datetime import datetime
from pydantic import BaseModel


# 예측 응답 (heatmap 포함 + is_new) — REQ-PRED-001
class AiAnalysisResponse(BaseModel):
    id: int
    record_id: int
    is_new: bool = False          # 응답 전용 (신규=True / 캐시 반환=False) — DB엔 없음
    is_pneumonia: bool
    confidence: float             # 0.00~100.00 (이미 퍼센트)
    heatmap_url: str | None       # Grad-CAM 실패 시 None
    ai_model: str
    created_at: datetime

    model_config = {"from_attributes": True}   # DB 객체 → 응답 자동 변환


# 목록 응답 (heatmap 제외) — REQ-PRED-002
class AiAnalysisListItem(BaseModel):
    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float
    ai_model: str
    created_at: datetime

    model_config = {"from_attributes": True}
