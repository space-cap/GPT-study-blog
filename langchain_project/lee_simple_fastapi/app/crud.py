"""
CRUD (Create, Read, Update, Delete) 작업 정의
데이터베이스와의 모든 상호작용을 담당
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas

# ===== User CRUD =====


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """ID로 사용자 조회"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """사용자명으로 사용자 조회"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """이메일로 사용자 조회"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """사용자 목록 조회 (페이지네이션)"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """새 사용자 생성"""
    # Pydantic 모델을 딕셔너리로 변환
    db_user = models.User(**user.model_dump())

    # 데이터베이스에 추가
    db.add(db_user)
    db.commit()  # 변경사항 커밋
    db.refresh(db_user)  # 생성된 ID 등 최신 정보 갱신

    return db_user


def update_user(
    db: Session, user_id: int, user_update: schemas.UserUpdate
) -> Optional[models.User]:
    """사용자 정보 업데이트"""
    # 기존 사용자 조회
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # 업데이트할 데이터만 추출 (None이 아닌 값들만)
    update_data = user_update.model_dump(exclude_unset=True)

    # 각 필드 업데이트
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """사용자 삭제"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()

    return True


# ===== Item CRUD =====


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    """ID로 아이템 조회"""
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items(
    db: Session, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None
) -> List[models.Item]:
    """아이템 목록 조회 (페이지네이션, 소유자 필터링 가능)"""
    query = db.query(models.Item)

    # 소유자 ID로 필터링 (선택사항)
    if owner_id:
        query = query.filter(models.Item.owner_id == owner_id)

    return query.offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate, owner_id: int) -> models.Item:
    """새 아이템 생성"""
    # 아이템 데이터에 소유자 ID 추가
    item_data = item.model_dump()
    item_data["owner_id"] = owner_id

    db_item = models.Item(**item_data)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_item(
    db: Session, item_id: int, item_update: schemas.ItemUpdate
) -> Optional[models.Item]:
    """아이템 정보 업데이트"""
    db_item = get_item(db, item_id)
    if not db_item:
        return None

    # 업데이트할 데이터만 추출
    update_data = item_update.model_dump(exclude_unset=True)

    # 각 필드 업데이트
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)

    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    """아이템 삭제"""
    db_item = get_item(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()

    return True


def get_items_by_user(db: Session, user_id: int) -> List[models.Item]:
    """특정 사용자의 모든 아이템 조회"""
    return db.query(models.Item).filter(models.Item.owner_id == user_id).all()
