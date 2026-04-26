from pydantic import BaseModel

class ProductBase(BaseModel):
    title: str
    description: str | None = None
    price: float
    in_stock: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: int

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True