from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/products/")
async def create_product(product: models.Product):
    # Insert product into the SQLite database
    c.execute("""INSERT INTO products (name, description, price) VALUES (?, ?, ?)""", 
              (product.name, product.description, product.price))
    conn.commit()
    return {"status": "Product created"}

@app.get("/products/")
async def read_products():
    # Fetch all products from the SQLite database
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return rows

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: models.Product):
    # Update the product in the SQLite database
    c.execute("""UPDATE products SET name=?, description=?, price=? WHERE id=?""", 
              (product.name, product.description, product.price, product_id))
    conn.commit()
    return {"status": "Product updated"}

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    # Delete the product from the SQLite database
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    return {"status": "Product deleted"}