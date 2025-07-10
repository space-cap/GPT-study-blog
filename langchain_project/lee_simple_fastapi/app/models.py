"""
SQLAlchemy 데이터베이스 모델 정의
User와 Item 테이블 구조 정의
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """
    사용자 테이블 모델
    """

    __tablename__ = "users"

    # 기본키: 자동 증가하는 정수
    id = Column(Integer, primary_key=True, index=True)

    # 사용자명: 고유값, 인덱스 설정
    username = Column(String, unique=True, index=True, nullable=False)

    # 이메일: 고유값, 인덱스 설정
    email = Column(String, unique=True, index=True, nullable=False)

    # 전체 이름: 선택사항
    full_name = Column(String, nullable=True)

    # 활성화 상태: 기본값 True
    is_active = Column(Boolean, default=True)

    # 생성일시: 자동으로 현재 시간 설정
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정: 한 사용자가 여러 아이템을 가질 수 있음
    items = relationship("Item", back_populates="owner")


class Item(Base):
    """
    아이템 테이블 모델
    """

    __tablename__ = "items"

    # 기본키: 자동 증가하는 정수
    id = Column(Integer, primary_key=True, index=True)

    # 아이템 이름: 필수값, 인덱스 설정
    name = Column(String, index=True, nullable=False)

    # 설명: 선택사항
    description = Column(String, nullable=True)

    # 가격: 필수값
    price = Column(Float, nullable=False)

    # 할인 여부: 기본값 False
    is_offer = Column(Boolean, default=False)

    # 소유자 ID: User 테이블의 외래키
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 생성일시: 자동으로 현재 시간 설정
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정: 아이템은 한 명의 소유자를 가짐
    owner = relationship("User", back_populates="items")
