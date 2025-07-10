from fastapi import APIRouter

from app.api.v1.endpoints import items, users, auth, upload

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
