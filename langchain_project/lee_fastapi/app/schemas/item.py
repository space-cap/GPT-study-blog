from typing import Optional
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: Optional[str] = Field(None, max_length=500, description="아이템 설명")
    price: float = Field(..., gt=0, description="아이템 가격")
    is_offer: bool = Field(False, description="할인 여부")


class ItemCreate(ItemBase):
    tax: Optional[float] = Field(None, ge=0, description="세금")


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_offer: Optional[bool] = None
    tax: Optional[float] = Field(None, ge=0)


class ItemInDBBase(ItemBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class Item(ItemInDBBase):
    pass


class ItemResponse(ItemInDBBase):
    price_with_tax: Optional[float] = None
