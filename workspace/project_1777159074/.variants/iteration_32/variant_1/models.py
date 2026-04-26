from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    id: int
    name: str
    price: float
    description: str
    image_url: str
    stock_quantity: int

    class Config:
        orm_mode = True