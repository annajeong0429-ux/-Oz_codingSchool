# app/repositories/ai_analysis_repositories.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AiAnalysisResult


# 캐싱 조회 (REQ-PRED-001 핵심): 같은 (진료기록, 모델) 결과가 있으면 반환, 없으면 None
async def get_by_record_and_model(
    db: AsyncSession, record_id: int, ai_model: str
) -> AiAnalysisResult | None:
    result = await db.execute(
        select(AiAnalysisResult)
        .where(
            AiAnalysisResult.record_id == record_id,
            AiAnalysisResult.ai_model == ai_model,
        )
        .order_by(AiAnalysisResult.created_at.desc())
    )
    return result.scalars().first()   # 있으면 최신 1개, 없으면 None


# 목록 조회 (REQ-PRED-002): 해당 진료기록의 모든 예측 결과
async def list_by_record(db: AsyncSession, record_id: int) -> list[AiAnalysisResult]:
    result = await db.execute(
        select(AiAnalysisResult)
        .where(AiAnalysisResult.record_id == record_id)
        .order_by(AiAnalysisResult.created_at.desc())   # ← 추가 (최신순)
    )
    return list(result.scalars().all())


# 저장
async def create(
    db: AsyncSession,
    record_id: int,
    is_pneumonia: bool,
    confidence: float,
    heatmap_url: str | None,
    ai_model: str,
) -> AiAnalysisResult:
    analysis = AiAnalysisResult(
        record_id=record_id,
        is_pneumonia=is_pneumonia,
        confidence=confidence,
        heatmap_url=heatmap_url,   # None이면 그대로 NULL 저장
        ai_model=ai_model,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
