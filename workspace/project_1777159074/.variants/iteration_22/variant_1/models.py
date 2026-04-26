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
    
    products = []
    for row in rows:
        product = Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4])
        products.append(product)
        
    conn.close()
    
    return products

def get_product_by_id(id: int):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    row = cursor.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    
    product = None if row is None else Product(id=row[0], name=row[1], description=row[2], price=row[3], image_url=row[4])
        
    conn.close()
    
    return product