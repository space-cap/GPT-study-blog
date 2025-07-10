"""
데이터베이스 연결 및 세션 관리
SQLite를 사용하여 간단하게 구성
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 환경변수에서 데이터베이스 URL 가져오기 (기본값: SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# SQLAlchemy 엔진 생성
# check_same_thread=False: SQLite에서 멀티스레드 사용 허용
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# 세션 팩토리 생성
# autocommit=False: 수동으로 커밋 관리
# autoflush=False: 수동으로 플러시 관리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 모델의 기본 클래스
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI의 Depends에서 사용
    """
    db = SessionLocal()
    try:
        yield db  # 세션 반환
    finally:
        db.close()  # 요청 완료 후 세션 종료
