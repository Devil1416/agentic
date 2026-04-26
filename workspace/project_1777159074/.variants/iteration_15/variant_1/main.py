from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/products")
async def read_products():
    c.execute("SELECT * FROM products")
    return {"data": c.fetchall()}

@app.post("/product")
async def create_product(product: models.Product):
    product = dict(product)
    keys = ', '.join(product.keys())
    values = ', '.join([f':{key}' for key in product.keys()])
    
    query = f"INSERT INTO products ({keys}) VALUES ({values})"
    c.execute(query, product)
    conn.commit()
    return {"status": "success"}

@app.put("/product/{id}")
async def update_product(id: int, product: models.Product):
    product = dict(product)
    updates = ', '.join([f'{key}=:{key}' for key in product.keys()])
    
    query = f"UPDATE products SET {updates} WHERE id=:id"
    product['id'] = id
    c.execute(query, product)
    conn.commit()
    return {"status": "success"}

@app.delete("/product/{id}")
async def delete_product(id: int):
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return {"status": "success"}