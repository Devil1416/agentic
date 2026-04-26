from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    quantity_in_stock: int | None = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: int

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True