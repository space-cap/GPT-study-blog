from fastapi import FastAPI

# FastAPI 인스턴스 생성
app = FastAPI()


# 루트 엔드포인트
@app.get("/")
def read_root():
    return {"Hello": "World", "iam":"python"}


# 경로 매개변수가 있는 엔드포인트
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
