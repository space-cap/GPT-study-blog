from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Project"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI project with best practices"
    API_V1_STR: str = "/api/v1"

    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./app.db"

    # 보안 설정
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY: str = "your-secret-api-key"

    # CORS 설정
    ALLOWED_HOSTS: List[str] = ["*"]

    # 로깅 설정
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
