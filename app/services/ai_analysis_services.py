# app/services/ai_analysis_services.py
import asyncio
import json
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage
from app.core.config import settings
from app.core.redis_client import get_redis
from app.repositories import ai_analysis_repositories as repo

QUEUE_NAME = "predictions"     # 작업 큐(List) — §7-2 #2
RESULT_TIMEOUT = 30            # 결과 대기 타임아웃(초) — §7-2 #9


# 예측 (or 캐시 반환) — REQ-PRED-001
# 흐름: 캐시확인 → subscribe → LPUSH → 결과대기 → DB저장 → 반환
async def predict_or_get_cached(db: AsyncSession, record_id: int):
    # 1. 진료기록 존재 확인 (404)
    record = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    if record.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="해당 진료기록을 찾을 수 없습니다.")

    # 2. 대표 X-ray 1장 조회 (404)
    xray_result = await db.execute(
        select(XrayImage).where(XrayImage.record_id == record_id).order_by(XrayImage.id).limit(1)
    )
    xray = xray_result.scalars().first()
    if xray is None:
        raise HTTPException(status_code=404, detail="예측할 X-Ray 이미지가 없습니다.")

    # 3. 캐싱 확인 (§7-2 #10): 같은 (진료기록, 모델) 결과 있으면 재추론 X → 즉시 반환
    cached = await repo.get_by_record_and_model(db, record_id, settings.AI_MODEL_NAME)
    if cached is not None:
        return cached, False          # is_new=False → 200 OK

    # 4. 작업 등록 + 결과 구독 (raw Redis)
    redis = get_redis()
    task_id = uuid.uuid4().hex
    channel = f"task:{task_id}"        # §7-2 #5

    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)    # ★ enqueue '전에' subscribe (§7-2 #8 — pub/sub 유실 방지)
    try:
        # 큐에 작업 등록 (LPUSH) — §7-2 #1·#4
        await redis.lpush(QUEUE_NAME, json.dumps({
            "task_id": task_id,
            "record_id": record_id,
            "image_path": xray.image_url,
        }))
        # 결과 대기 (타임아웃 30s) — §7-2 #8
        result = await _wait_for_result(pubsub, RESULT_TIMEOUT)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    if result is None:                 # 타임아웃 (워커 응답 없음) — §7-2 #9
        raise HTTPException(status_code=504, detail="AI 예측 시간 초과 (워커 응답 없음)")
    if result.get("status") == "failed":   # 워커 실패 보고 — §7-2 #7
        raise HTTPException(status_code=500, detail=f"AI 예측 실패: {result.get('error')}")

    # 5. 결과 DB 저장 (§7-2 #11: 저장 주체 = FastAPI)
    saved = await repo.create(
        db,
        record_id=record_id,
        is_pneumonia=result["is_pneumonia"],
        confidence=result["confidence"],
        heatmap_url=result["heatmap_url"],
        ai_model=result["model_name"],
    )
    return saved, True                 # is_new=True → 201 Created


async def _wait_for_result(pubsub, timeout: int) -> dict | None:
    """결과 채널에서 메시지 1건을 timeout(초) 안에 받으면 dict, 못 받으면 None"""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            return None
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=remaining)
        if msg and msg.get("type") == "message":
            return json.loads(msg["data"])   # decode_responses=True라 str


# 목록 조회 — REQ-PRED-002 (변경 없음)
async def list_analyses(db: AsyncSession, record_id: int) -> list:
    record = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    if record.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="해당 진료기록을 찾을 수 없습니다.")
    return await repo.list_by_record(db, record_id)

