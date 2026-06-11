import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.apis import practice_apis
from app.apis import user_apis          
from app.apis import patient_apis       
from app.apis import ai_analysis_apis   
from app.apis import medical_record_apis
from app.worker.model import load_models


# 서버 시작/종료 이벤트 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 모델 로딩
    load_models()
    yield
    # 서버 종료 시 (필요시 정리 작업)

app = FastAPI(lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent.parent

if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")

app.include_router(practice_apis.router)
app.include_router(user_apis.router)
app.include_router(patient_apis.router)
app.include_router(ai_analysis_apis.router)   
app.include_router(medical_record_apis.router)

@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
    ):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")
