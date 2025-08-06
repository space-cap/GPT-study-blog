"""
사용자 데이터 모델 정의
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class UserInfo(BaseModel):
    """사용자 기본 정보 모델"""

    name: Optional[str] = None
    phone: Optional[str] = None
    symptoms: Optional[str] = None

    @field_validator("name")
    def validate_name(cls, v):
        if v and (len(v) < 2 or len(v) > 10):
            raise ValueError("이름은 2-10자 사이여야 합니다.")
        return v

    @field_validator("phone")
    def validate_phone(cls, v):
        if v and not v.startswith("010"):
            raise ValueError("올바른 전화번호 형식이 아닙니다.")
        return v


class CustomerData(BaseModel):
    """고객 데이터 모델 (데이터베이스 저장용)"""

    name: str
    phone: str
    consent_date: str
    symptoms: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConsentInfo(BaseModel):
    """개인정보 동의 정보 모델"""

    consent_given: bool = False
    consent_timestamp: Optional[str] = None
    consent_type: str = "personal_info_collection"

    @field_validator("consent_timestamp")
    def validate_timestamp(cls, v):
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("올바른 timestamp 형식이 아닙니다.")
        return v
