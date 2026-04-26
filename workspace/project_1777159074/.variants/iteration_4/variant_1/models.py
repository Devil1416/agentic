import sqlite3
from typing import Optional
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: Optional[str] = None

def create_product(product: Product) -> bool:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = """INSERT INTO products (name, description, price, image_url) 
               VALUES (?, ?, ?, ?);"""
    cursor.execute(query, (product.name, product.description, product.price, product.image_url))
    conn.commit()
    
    return True if cursor.rowcount > 0 else False

def get_all_products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM products;"
    cursor.execute(query)
    
    return cursor.fetchall()

def get_product_by_id(id: int):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE id=?;"
    cursor.execute(query, (id,))
    
    return cursor.fetchone()

def update_product(product: Product) -> bool:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = """UPDATE products 
               SET name=?, description=?, price=?, image_url=? 
               WHERE id=?;"""
    cursor.execute(query, (product.name, product.description, product.price, product.image_url, product.id))
    conn.commit()
    
    return True if cursor.rowcount > 0 else False

def delete_product(id: int) -> bool:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = "DELETE FROM products WHERE id=?;"
    cursor.execute(query, (id,))
    conn.commit()
    
    return True if cursor.rowcount > 0 else False