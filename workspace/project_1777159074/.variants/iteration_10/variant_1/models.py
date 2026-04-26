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
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS products 
                    (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, image_url TEXT)""")
    
    conn.commit()
    conn.close()

def get_product(product_id: int):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    row = cursor.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    
    if row is not None:
        return Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4])
    
    conn.close()

def get_all_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    rows = cursor.execute("SELECT * FROM products").fetchall()
    
    products = [Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4]) for row in rows]
    
    conn.close()
    
    return products

def create_product(product: Product):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", 
                   (product.name, product.description, product.price, product.image_url))
    
    conn.commit()
    conn.close()

def update_product(product: Product):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE products SET name=?, description=?, price=?, image_url=? WHERE id=?", 
                   (product.name, product.description, product.price, product.image_url, product.id))
    
    conn.commit()
    conn.close()

def delete_product(product_id: int):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    
    conn.commit()
    conn.close()