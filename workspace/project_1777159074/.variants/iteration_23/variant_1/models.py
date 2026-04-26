import sqlite3
from typing import Optional
from pydantic import BaseModel

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: int

class ProductInDB(ProductBase):
    id: int

def get_product(id: int, db: sqlite3.Connection):
    cursor = db.cursor()
    result = cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    row = result.fetchone()
    if row is None:
        return None
    return ProductInDB(**row)

def get_products(db: sqlite3.Connection):
    cursor = db.cursor()
    results = cursor.execute("SELECT * FROM products")
    rows = results.fetchall()
    return [ProductInDB(**row) for row in rows]

def create_product(p: ProductCreate, db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO products (title, description, price, image_url) VALUES (?, ?, ?, ?)
    """, (p.title, p.description, p.price, p.image_url))
    db.commit()
    id = cursor.lastrowid
    return ProductInDB(**{**p.dict(), "id": id})

def update_product(p: ProductUpdate, db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute("""
        UPDATE products SET title=?, description=?, price=?, image_url=? WHERE id=?
    """, (p.title, p.description, p.price, p.image_url, p.id))
    db.commit()
    return get_product(p.id, db)

def delete_product(id: int, db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    db.commit()