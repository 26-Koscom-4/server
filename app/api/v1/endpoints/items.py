from typing import List
from fastapi import APIRouter
from app.domain.common.schema.item import ItemCreate, ItemRead

router = APIRouter()

_fake_db: List[ItemRead] = []

@router.get("/", response_model=List[ItemRead])
def list_items() -> List[ItemRead]:
    return _fake_db

@router.post("/", response_model=ItemRead, status_code=201)
def create_item(payload: ItemCreate) -> ItemRead:
    item = ItemRead(id=len(_fake_db) + 1, **payload.dict())
    _fake_db.append(item)
    return item
