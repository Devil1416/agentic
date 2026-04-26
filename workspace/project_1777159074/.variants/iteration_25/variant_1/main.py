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
def create_product(product: models.Product):
    # Insert product into the database
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
              (product.name, product.description, product.price))
    conn.commit()
    return {"status": "ok"}

@app.get("/products/")
def read_products():
    # Fetch all products from the database
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return {"products": rows}

@app.put("/products/{product_id}")
def update_product(product_id: int, product: models.Product):
    # Update the product in the database
    c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", 
              (product.name, product.description, product.price, product_id))
    conn.commit()
    return {"status": "ok"}

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    # Delete the product from the database
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    return {"status": "ok"}