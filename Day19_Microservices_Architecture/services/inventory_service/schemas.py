from pydantic import BaseModel
from typing import Optional

class ItemCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = ""
    price: float
    stock_quantity: int
    category: Optional[str] = "general"

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None

class StockUpdate(BaseModel):
    delta: int

class ItemResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    category: Optional[str]

