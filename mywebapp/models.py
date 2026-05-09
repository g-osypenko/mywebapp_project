from datetime import datetime
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(..., description="Назва предмета")
    quantity: int = Field(..., ge=0, description="Кількість")


class ItemList(BaseModel):
    id: int
    name: str


class ItemDetail(BaseModel):
    id: int
    name: str
    quantity: int
    created_at: datetime