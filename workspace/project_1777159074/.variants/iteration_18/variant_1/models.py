import sqlite3
from typing import Optional
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: str

def create_product_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS products 
                      (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, image_url TEXT)""")
    conn.commit()
    conn.close()

def create_product(name: str, description: str, price: float, image_url: str):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("""INSERT INTO products (name, description, price, image_url) 
                      VALUES (?, ?, ?, ?)""", (name, description, price, image_url))
    conn.commit()
    conn.close()

def get_product(id: int) -> Optional[Product]:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    row = cursor.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    if row is None:
        return None
    
    product = Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4])
    conn.close()
    return product

def update_product(id: int, name: str, description: str, price: float, image_url: str):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("""UPDATE products 
                      SET name=?, description=?, price=?, image_url=? 
                      WHERE id=?""", (name, description, price, image_url, id))
    conn.commit()
    conn.close()

def delete_product(id: int):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()