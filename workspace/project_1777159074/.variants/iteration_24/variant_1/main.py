from fastapi import FastAPI
import sqlite3
from .models import Product

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('products.db')
c = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/product/")
async def create_product(product: Product):
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
              (product.name, product.description, product.price))
    conn.commit()
    return {"status": "Product created"}

@app.get("/products/")
async def read_products():
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return rows

@app.put("/product/{id}")
async def update_product(id: int, product: Product):
    c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", 
              (product.name, product.description, product.price, id))
    conn.commit()
    return {"status": "Product updated"}

@app.delete("/product/{id}")
async def delete_product(id: int):
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return {"status": "Product deleted"}