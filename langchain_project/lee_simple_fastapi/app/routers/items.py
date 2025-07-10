"""
아이템 관련 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas
from ..database import get_db

# 라우터 생성
router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED
)
def create_item(
    item: schemas.ItemCreate,
    owner_id: int = Query(..., description="아이템 소유자 ID"),
    db: Session = Depends(get_db),
):
    """
    새 아이템 생성

    - **name**: 아이템 이름 (1-100자)
    - **description**: 아이템 설명 (선택사항, 최대 500자)
    - **price**: 가격 (0보다 커야 함)
    - **is_offer**: 할인 여부 (기본값: false)
    - **owner_id**: 소유자 ID (쿼리 파라미터)
    """
    # 소유자 존재 확인
    if not crud.get_user(db, owner_id):
        raise HTTPException(status_code=404, detail="Owner not found")

    return crud.create_item(db=db, item=item, owner_id=owner_id)


@router.get("/", response_model=List[schemas.ItemResponse])
def read_items(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=100, description="가져올 레코드 수"),
    owner_id: Optional[int] = Query(None, description="특정 소유자의 아이템만 조회"),
    db: Session = Depends(get_db),
):
    """
    아이템 목록 조회 (페이지네이션, 소유자 필터링)

    - **skip**: 건너뛸 레코드 수 (기본값: 0)
    - **limit**: 가져올 레코드 수 (기본값: 100, 최대: 100)
    - **owner_id**: 특정 소유자의 아이템만 조회 (선택사항)
    """
    items = crud.get_items(db, skip=skip, limit=limit, owner_id=owner_id)
    return items


@router.get("/{item_id}", response_model=schemas.ItemWithOwner)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    특정 아이템 조회 (소유자 정보 포함)

    - **item_id**: 아이템 ID
    """
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db)
):
    """
    아이템 정보 업데이트

    - **item_id**: 아이템 ID
    - 업데이트할 필드만 포함하면 됨
    """
    updated_item = crud.update_item(db, item_id, item_update)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    아이템 삭제

    - **item_id**: 삭제할 아이템 ID
    """
    if not crud.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")

    return None


@router.get("/user/{user_id}", response_model=List[schemas.ItemResponse])
def read_user_items(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자의 모든 아이템 조회

    - **user_id**: 사용자 ID
    """
    # 사용자 존재 확인
    if not crud.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    items = crud.get_items_by_user(db, user_id)
    return items
