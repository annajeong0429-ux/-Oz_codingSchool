# app/core/redis_client.py
# FastAPI(생산자)용 Redis 비동기 클라이언트
import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """싱글톤 비동기 Redis 클라이언트 (앱 전체 공유)"""
    global _redis
    if _redis is None:
        # decode_responses=True → 메시지를 str로 받음 (json 처리 편함)
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis
