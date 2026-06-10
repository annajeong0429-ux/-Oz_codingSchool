# app/services/ai_analysis_services.py
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage
from app.worker.model import predict_pneumonia, MODEL_NAME
from app.repositories import ai_analysis_repositories as repo


# 예측 (or 캐시 반환) — REQ-PRED-001
# 반환: (AiAnalysisResult 객체, is_new) 튜플
async def predict_or_get_cached(db: AsyncSession, record_id: int):
    # 1. 진료기록 존재 확인 (없으면 404)
    record = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    if record.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="해당 진료기록을 찾을 수 없습니다.")

    # 2. 대표 X-ray 1장 조회 (여러 장이면 id 작은 것 = 대표) — 없으면 404
    xray_result = await db.execute(
        select(XrayImage).where(XrayImage.record_id == record_id).order_by(XrayImage.id)
    )
    xray = xray_result.scalars().first()
    if xray is None:
        raise HTTPException(status_code=404, detail="예측할 X-Ray 이미지가 없습니다.")

    # 3. 캐싱 확인: 같은 (진료기록, 모델) 결과 있으면 재추론 X (REQ-PRED-001 핵심)
    cached = await repo.get_by_record_and_model(db, record_id, MODEL_NAME)
    if cached is not None:
        return cached, False          # is_new=False → 200 OK

    # 4. 캐시 없음 → 대표 X-ray 파일을 읽어 bytes 로드
    try:
        with open(xray.image_url, "rb") as f:
            image_bytes = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="X-Ray 이미지 파일을 찾을 수 없습니다.")

    # 5. 예측 — 모델 추론은 무거운(blocking) 작업이라 threadpool에서 실행 (NFR-PRED-002, 3초)
    result = await run_in_threadpool(predict_pneumonia, image_bytes)

    # 6. 저장
    saved = await repo.create(
        db,
        record_id=record_id,
        is_pneumonia=result["is_pneumonia"],
        confidence=result["confidence"],     # 이미 퍼센트 → 변환 X
        heatmap_url=result["heatmap_url"],   # None이면 그대로 NULL
        ai_model=result["model_name"],       # 캐싱 키 ("convnext_densenet_OR")
    )
    return saved, True                # is_new=True → 201 Created


# 목록 조회 — REQ-PRED-002
async def list_analyses(db: AsyncSession, record_id: int) -> list:
    record = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    if record.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="해당 진료기록을 찾을 수 없습니다.")
    return await repo.list_by_record(db, record_id)
