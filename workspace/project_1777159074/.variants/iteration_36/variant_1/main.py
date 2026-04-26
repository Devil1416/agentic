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
    # Insert product into database
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
              (product.name, product.description, product.price))
    conn.commit()
    return {"status": "ok"}

@app.get("/products/")
async def read_products():
    # Fetch all products from the database
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return rows