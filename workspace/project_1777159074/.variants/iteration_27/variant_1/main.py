from fastapi import FastAPI
import sqlite3
from .models import Product

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/products")
def read_products():
    c.execute("SELECT * FROM products")
    return [Product(*row) for row in c.fetchall()]

@app.post("/product")
def create_product(product: Product):
    with conn:
        c.execute("""INSERT INTO products (name, description, price) VALUES (?, ?, ?)""", 
                  (product.name, product.description, product.price))
    return {"message": "Product created successfully"}

@app.put("/product/{id}")
def update_product(id: int, product: Product):
    with conn:
        c.execute("""UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?""", 
                  (product.name, product.description, product.price, id))
    return {"message": "Product updated successfully"}

@app.delete("/product/{id}")
def delete_product(id: int):
    with conn:
        c.execute("DELETE FROM products WHERE id = ?", (id,))
    return {"message": "Product deleted successfully"}