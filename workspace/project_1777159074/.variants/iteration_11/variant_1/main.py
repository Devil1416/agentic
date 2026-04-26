from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

# Connect to SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/products/")
async def create_product(product: models.Product):
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
              (product.name, product.description, product.price))
    conn.commit()
    return {"status": "ok"}

@app.get("/products/")
async def read_products():
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return rows

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: models.Product):
    c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?",
              (product.name, product.description, product.price, product_id))
    conn.commit()
    return {"status": "ok"}

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    return {"status": "ok"}