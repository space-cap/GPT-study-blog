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


@app.post("/users/")
def create_user(user: User):
    return {"message": "User created~~", "user": user}


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


@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate):
    return ItemResponse(**item.model_dump(), is_offer=True)
