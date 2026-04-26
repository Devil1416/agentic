import sqlite3
from typing import Optional
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: Optional[str] = None

def create_product_table():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, image_url TEXT)""")
    
    conn.commit()
    conn.close()

def insert_product(product: Product):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", 
              (product.name, product.description, product.price, product.image_url))
    
    conn.commit()
    conn.close()

def get_all_products():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    
    conn.close()
    
    return [Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4]) for row in rows]

def get_product(id: int):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    row = c.fetchone()
    
    conn.close()
    
    if row:
        return Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4])
    else:
        return None

def update_product(product: Product):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("UPDATE products SET name=?, description=?, price=?, image_url=? WHERE id=?", 
              (product.name, product.description, product.price, product.image_url, product.id))
    
    conn.commit()
    conn.close()

def delete_product(id: int):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM products WHERE id=?", (id,))
    
    conn.commit()
    conn.close()