# worker/redis_client.py
# 워커(소비자)용 동기 Redis 클라이언트
# FastAPI 쪽 async와 달리 워커는 단순 루프라 sync로 충분

import json
import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def dequeue(queue_name: str, timeout: int = 5) -> dict | None:
    """큐에서 작업 1개를 꺼냄. timeout초 동안 대기 후 없으면 None 반환."""
    result = get_redis().brpop(queue_name, timeout=timeout)
    if result is None:
        return None
    _, raw = result
    return json.loads(raw)


def publish_result(task_id: str, payload: dict) -> None:
    """워커 처리 결과를 task:{task_id} 채널에 publish."""
    get_redis().publish(f"task:{task_id}", json.dumps(payload))
