"""
사용자 관련 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

# 라우터 생성 (태그는 API 문서에서 그룹화에 사용)
router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    새 사용자 생성

    - **username**: 고유한 사용자명 (3-50자)
    - **email**: 고유한 이메일 주소
    - **full_name**: 전체 이름 (선택사항)
    """
    # 중복 사용자명 확인
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # 중복 이메일 확인
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    return crud.create_user(db=db, user=user)


@router.get("/", response_model=List[schemas.UserResponse])
def read_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=100, description="가져올 레코드 수"),
    db: Session = Depends(get_db),
):
    """
    사용자 목록 조회 (페이지네이션)

    - **skip**: 건너뛸 레코드 수 (기본값: 0)
    - **limit**: 가져올 레코드 수 (기본값: 100, 최대: 100)
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.UserWithItems)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자 조회 (소유한 아이템 포함)

    - **user_id**: 사용자 ID
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)
):
    """
    사용자 정보 업데이트

    - **user_id**: 사용자 ID
    - 업데이트할 필드만 포함하면 됨
    """
    # 기존 사용자 존재 확인
    if not crud.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    # 사용자명 중복 확인 (변경하는 경우)
    if user_update.username:
        existing_user = crud.get_user_by_username(db, user_update.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")

    # 이메일 중복 확인 (변경하는 경우)
    if user_update.email:
        existing_user = crud.get_user_by_email(db, user_update.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already taken")

    updated_user = crud.update_user(db, user_id, user_update)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    사용자 삭제

    - **user_id**: 삭제할 사용자 ID
    """
    if not crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    # 204 No Content는 응답 본문이 없음
    return None
