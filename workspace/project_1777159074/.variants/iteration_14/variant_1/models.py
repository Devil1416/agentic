from sqlalchemy import Column, Integer, String, Float
from api.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    description = Column(String(1024))
    price = Column(Float)