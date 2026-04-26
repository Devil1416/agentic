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
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS products 
                      (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, image_url TEXT)""")
    
    conn.commit()
    conn.close()

def insert_product(product: Product):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", 
                   (product.name, product.description, product.price, product.image_url))
    
    conn.commit()
    conn.close()

def get_all_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    rows = cursor.execute("SELECT * FROM products")
    products = [Product(*row) for row in rows]
    
    conn.close()
    return products

def get_product(id: int):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    row = cursor.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    product = Product(*row) if row else None
    
    conn.close()
    return product

def update_product(product: Product):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE products SET name=?, description=?, price=?, image_url=? WHERE id=?", 
                   (product.name, product.description, product.price, product.image_url, product.id))
    
    conn.commit()
    conn.close()

def delete_product(id: int):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    
    conn.commit()
    conn.close()