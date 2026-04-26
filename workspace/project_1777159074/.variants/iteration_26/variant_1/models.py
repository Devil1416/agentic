import sqlite3
from typing import Optional
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: Optional[str] = None

def get_db_connection():
    conn = sqlite3.connect('database.sqlite')
    return conn

def create_product(product: Product):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (product.name, product.description, product.price, product.image_url))
        conn.commit()

def read_products():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM products"
        cursor.execute(query)
        return cursor.fetchall()

def update_product(id: int, product: Product):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "UPDATE products SET name=?, description=?, price=?, image_url=? WHERE id=?"
        cursor.execute(query, (product.name, product.description, product.price, product.image_url, id))
        conn.commit()

def delete_product(id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "DELETE FROM products WHERE id=?"
        cursor.execute(query, (id,))
        conn.commit()