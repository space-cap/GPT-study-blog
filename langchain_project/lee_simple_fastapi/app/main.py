"""
FastAPI 메인 애플리케이션
모든 라우터와 설정을 통합
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import users, items

# 데이터베이스 테이블 생성
# 실제 운영에서는 Alembic 등의 마이그레이션 도구 사용 권장
Base.metadata.create_all(bind=engine)

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Simple FastAPI CRUD",
    description="User와 Item을 관리하는 간단한 CRUD API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 경로
    redoc_url="/redoc",  # ReDoc 경로
)

# CORS 미들웨어 설정 (프론트엔드와의 통신을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")


@app.get("/")
def read_root():
    """
    루트 엔드포인트
    API 상태 확인용
    """
    return {
        "message": "Welcome to Simple FastAPI CRUD",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트
    서버 상태 확인용
    """
    return {"status": "healthy"}
