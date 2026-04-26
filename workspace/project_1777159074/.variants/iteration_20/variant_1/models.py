import sqlite3
from typing import List, Optional
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    image_url: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: int

class ProductInDB(ProductBase):
    id: int

def get_db_connection():
    conn = sqlite3.connect('sqlite_database.db')
    return conn

def get_product(id: int) -> Optional[ProductInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = result.fetchone()
    if product is None:
        return None
    return ProductInDB(id=product[0], name=product[1], description=product[2], price=product[3], image_url=product[4])

def get_products() -> List[ProductInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = cursor.execute("SELECT * FROM products")
    products = results.fetchall()
    return [ProductInDB(id=product[0], name=product[1], description=product[2], price=product[3], image_url=product[4]) for product in products]

def create_product(product: ProductCreate) -> Optional[ProductInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", 
                            (product.name, product.description, product.price, product.image_url))
    if result.rowcount == 0:
        return None
    conn.commit()
    return ProductInDB(id=result.lastrowid, name=product.name, description=product.description, price=product.price, image_url=product.image_url)

def update_product(product: ProductUpdate) -> Optional[ProductInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute("UPDATE products SET name=?, description=?, price=?, image_url=? WHERE id=?", 
                            (product.name, product.description, product.price, product.image_url, product.id))
    if result.rowcount == 0:
        return None
    conn.commit()
    return ProductInDB(id=product.id, name=product.name, description=product.description, price=product.price, image_url=product.image_url)

def delete_product(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute("DELETE FROM products WHERE id=?", (id,))
    if result.rowcount == 0:
        return None
    conn.commit()