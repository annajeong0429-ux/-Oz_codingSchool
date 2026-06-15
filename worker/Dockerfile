# worker/Dockerfile
# app/Dockerfile과 같은 베이스 이미지 사용 (model.py 공유)
FROM python:3.12-slim

# torch OpenMP + asyncmy 컴파일 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

CMD ["python", "worker/main.py"]
