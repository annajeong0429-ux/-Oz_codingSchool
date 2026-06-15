# worker/main.py
# AI 추론 워커 — Redis 큐에서 작업을 꺼내 추론 후 결과를 Pub/Sub으로 publish
# §7-2 인터페이스 계약 기준:
#   큐: BRPOP predictions
#   메시지: {"task_id", "record_id", "image_path"}
#   결과 채널: task:{task_id}
#   DB 저장: FastAPI가 담당 (워커는 publish만)

import logging
import sys

# PYTHONPATH=/app 덕분에 app 패키지 import 가능
from app.worker.model import predict_pneumonia, load_models
from worker.redis_client import dequeue, publish_result

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

QUEUE_NAME = "predictions"


def process(task: dict) -> None:
    task_id = task["task_id"]
    record_id = task["record_id"]
    image_path = task["image_path"]

    log.info("작업 시작 task_id=%s record_id=%s", task_id, record_id)

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except FileNotFoundError:
        log.error("X-Ray 파일 없음: %s", image_path)
        publish_result(task_id, {"status": "failed", "error": f"파일 없음: {image_path}"})
        return

    try:
        result = predict_pneumonia(image_bytes)
        publish_result(task_id, {
            "status": "completed",
            "is_pneumonia": result["is_pneumonia"],
            "confidence": result["confidence"],
            "heatmap_url": result["heatmap_url"],
            "model_name": result["model_name"],
        })
        log.info("작업 완료 task_id=%s is_pneumonia=%s", task_id, result["is_pneumonia"])

    except Exception as e:
        log.exception("추론 실패 task_id=%s", task_id)
        publish_result(task_id, {"status": "failed", "error": str(e)})


def main() -> None:
    log.info("AI 워커 시작 — 큐: %s", QUEUE_NAME)
    load_models()                # ★ 모델 로딩 (워커가 추론하므로 필수)
    while True:
        task = dequeue(QUEUE_NAME, timeout=5)
        if task is None:
            continue
        process(task)


if __name__ == "__main__":
    main()
