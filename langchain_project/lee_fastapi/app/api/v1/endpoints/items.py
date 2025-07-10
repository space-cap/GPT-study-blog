from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.item import item_crud
from app.schemas.item import Item, ItemCreate, ItemUpdate, ItemResponse
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=List[ItemResponse])
def read_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    q: Optional[str] = Query(None, min_length=3, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """아이템 목록 조회"""
    items = item_crud.get_multi(db, skip=skip, limit=limit, search=q)
    return items


@router.get("/{item_id}", response_model=ItemResponse)
def read_item(
    item_id: int = Path(..., gt=0, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 아이템 조회"""
    item = item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """새 아이템 생성"""
    item = item_crud.create(db, obj_in=item_in, owner_id=current_user.id)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int = Path(..., gt=0),
    item_in: ItemUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """아이템 업데이트"""
    item = item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item = item_crud.update(db, db_obj=item, obj_in=item_in)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """아이템 삭제"""
    item = item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_crud.remove(db, id=item_id)
    return None
