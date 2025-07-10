from fastapi import FastAPI

# FastAPI 인스턴스 생성
app = FastAPI()


# 루트 엔드포인트
@app.get("/")
def read_root():
    return {"Hello": "World", "iam": "python"}


# 경로 매개변수가 있는 엔드포인트
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


from pydantic import BaseModel
from typing import Optional


class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None
    description: Optional[str] = None


class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


@app.post("/items/")
def create_item(item: Item):
    return {"item_name": item.name, "item_price": item.price}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}


@app.get("/users/")
def get_users(skip: int = 0, limit: int = 10):
    return {"users": f"skip: {skip}, limit: {limit}"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

"""
@app.post("/users/")
def create_user(user: User):
    return {"message": "User created~~", "user": user}
"""

@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    return {"user_id": user_id, "user": user}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    return {"message": f"User {user_id} deleted"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}


# 경로 매개변수 검증
from fastapi import Path


@app.get("/items/{item_id}")
def read_item(item_id: int = Path(..., gt=0, le=1000)):
    return {"item_id": item_id}


@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, q: Optional[str] = None):
    return {"skip": skip, "limit": limit, "q": q}


# 쿼리 매개변수 검증
from fastapi import Query


@app.get("/items/")
def read_items(
    q: Optional[str] = Query(None, min_length=3, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
):
    return {"q": q, "skip": skip, "limit": limit}

from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


@app.post("/items/")
def create_item(item: ItemCreate):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict

from fastapi import File, UploadFile
from typing import List

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}


class ItemResponse(BaseModel):
    name: str
    price: float
    is_offer: bool = False

"""
버전별 차이점
Pydantic v1
dict() 메서드 사용 가능
json() 메서드로 JSON 직렬화

Pydantic v2 (현재 권장)
model_dump(): 딕셔너리로 변환
model_dump_json(): JSON 문자열로 변환
model_copy(): 모델 복사
"""

@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate):
    return ItemResponse(**item.model_dump(), is_offer=True)

from fastapi import status


@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    return None

from fastapi import HTTPException


@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}


from fastapi import Request
from fastapi.responses import JSONResponse


class CustomException(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=418, content={"message": f"Oops! {exc.name} did something wrong."}
    )

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
from fastapi import Request


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["lee-Time"] = str(process_time)
    return response


from fastapi import Depends


def common_parameters(q: Optional[str] = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
def read_items(commons: dict = Depends(common_parameters)):
    return commons


@app.get("/users/")
def read_users(commons: dict = Depends(common_parameters)):
    return commons

"""
클래스 기반 의존성
"""
class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


@app.get("/items/")
def read_items(commons: CommonQueryParams = Depends(CommonQueryParams)):
    return commons


from fastapi import Security
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


@app.get("/protected/")
def protected_route(api_key: str = Depends(get_api_key)):
    return {"message": "This is a protected route"}

"""
JWT란?
JWT(JSON Web Token)는 당사자 간에 정보를 JSON 객체로 안전하게 전송하기 위한 개방형 표준(RFC 7519)입니다. 
주로 인증과 정보 교환에 사용됩니다.
"""
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, "secret", algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/protected/")
def protected_route(current_user: dict = Depends(verify_token)):
    return {"message": f"Hello {current_user.get('username')}"}


from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 모델 정의
class UserDb(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)


Base.metadata.create_all(bind=engine)


# 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic 모델들
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


# API 엔드포인트
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
