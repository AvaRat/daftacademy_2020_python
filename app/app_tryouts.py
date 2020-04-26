from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

app = FastAPI()


@app.get("/users/{user_id}")
async def read_user_item(user_id: int, item_id: str, q: str = None, short: bool = False):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/items/{item_id}")
async def read_user_item(item_id: str, needy: str, skip: int = 0, limit: int = None):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item


@app.post("/items/{item_id}/{item_price}/{name}")
async def create_item(item_id:int, item_price:float, name:str):
    return {'ID':item_id, 'PRICE':item_price, 'NAME':name}

#@app.post("/items/{item_id}")
#async def create_item(item_id: int, item: Item):
#    return {"item_id": item_id, **item.dict()}