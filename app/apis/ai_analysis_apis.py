# app/apis/ai_analysis_apis.py
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.ai_analysis_schemas import AiAnalysisResponse, AiAnalysisListItem
from app.services import ai_analysis_services as service

router = APIRouter(prefix="/api/v1/medical-records", tags=["ai-analysis"])


# AI 폐렴 예측 (or 캐시 반환) — REQ-PRED-001
@router.post(
    "/{record_id}/ai-analysis",
    summary="AI 폐렴 예측",
    response_model=AiAnalysisResponse,
    status_code=status.HTTP_201_CREATED,   # 기본(신규). 캐시면 아래에서 200으로 덮음
)
async def predict_handler(
    record_id: int,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    obj, is_new = await service.predict_or_get_cached(db, record_id)
    # 신규=201, 캐시=200 분기
    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return AiAnalysisResponse(
        id=obj.id,
        record_id=obj.record_id,
        is_new=is_new,
        is_pneumonia=obj.is_pneumonia,
        confidence=float(obj.confidence),    # Decimal → float
        heatmap_url=obj.heatmap_url,
        ai_model=obj.ai_model,
        created_at=obj.created_at,
    )


# 예측 결과 목록 조회 — REQ-PRED-002
@router.get(
    "/{record_id}/ai-analysis",
    summary="AI 예측 결과 목록 조회",
    response_model=list[AiAnalysisListItem],
)
async def list_handler(
    record_id: int,
    db: AsyncSession = Depends(async_get_db),
):
    return await service.list_analyses(db, record_id)
