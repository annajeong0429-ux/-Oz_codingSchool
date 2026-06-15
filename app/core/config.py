from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASSWORD: str = "password0000"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://localhost:6379/0"   # compose에선 redis://redis:6379/0 주입
    AI_MODEL_NAME: str = "convnext_densenet_OR"    # 캐싱 키 (model.py의 MODEL_NAME과 일치)

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
