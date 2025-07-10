"""
Pydantic 스키마 정의
API 요청/응답 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ===== User 스키마 =====


class UserBase(BaseModel):
    """사용자 기본 스키마"""

    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: str = Field(..., description="이메일 주소")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")


class UserCreate(UserBase):
    """사용자 생성 스키마"""

    pass


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마 (모든 필드 선택사항)"""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """사용자 응답 스키마"""

    id: int
    is_active: bool
    created_at: datetime

    class Config:
        # SQLAlchemy 모델과 호환
        from_attributes = True


class UserWithItems(UserResponse):
    """아이템을 포함한 사용자 응답 스키마"""

    items: List["ItemResponse"] = []


# ===== Item 스키마 =====


class ItemBase(BaseModel):
    """아이템 기본 스키마"""

    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: Optional[str] = Field(None, max_length=500, description="아이템 설명")
    price: float = Field(..., gt=0, description="가격 (0보다 커야 함)")
    is_offer: bool = Field(False, description="할인 여부")


class ItemCreate(ItemBase):
    """아이템 생성 스키마"""

    pass


class ItemUpdate(BaseModel):
    """아이템 업데이트 스키마 (모든 필드 선택사항)"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_offer: Optional[bool] = None


class ItemResponse(ItemBase):
    """아이템 응답 스키마"""

    id: int
    owner_id: int
    created_at: datetime

    class Config:
        # SQLAlchemy 모델과 호환
        from_attributes = True


class ItemWithOwner(ItemResponse):
    """소유자 정보를 포함한 아이템 응답 스키마"""

    owner: UserResponse


# 순환 참조 해결을 위한 모델 업데이트
UserWithItems.model_rebuild()
