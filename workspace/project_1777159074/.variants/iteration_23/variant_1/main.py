from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/products")
def read_products():
    c.execute("SELECT * FROM products")
    return {"data": c.fetchall()}

@app.post("/products")
def create_product(product: models.Product):
    product = product.dict()
    c.execute("""INSERT INTO products (name, description, price) VALUES (?, ?, ?)""", 
              (product['name'], product['description'], product['price']))
    conn.commit()
    return {"message": "Product created"}

@app.put("/products/{id}")
def update_product(id: int, product: models.Product):
    product = product.dict()
    c.execute("""UPDATE products SET name=?, description=?, price=? WHERE id=?""", 
              (product['name'], product['description'], product['price'], id))
    conn.commit()
    return {"message": "Product updated"}

@app.delete("/products/{id}")
def delete_product(id: int):
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return {"message": "Product deleted"}