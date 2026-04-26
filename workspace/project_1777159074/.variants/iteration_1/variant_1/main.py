from fastapi import FastAPI
import sqlite3
from .models import Product

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/products")
async def get_all_products():
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return {"products": rows}

@app.post("/product")
async def create_product(product: Product):
    product_data = f"(null, '{product.name}', {product.price}, {product.quantity})"
    c.execute(f"INSERT INTO products VALUES {product_data}")
    conn.commit()
    return {"message": "Product created"}

@app.put("/product/{id}")
async def update_product(id: int, product: Product):
    product_data = f"'{product.name}', {product.price}, {product.quantity}"
    c.execute(f"UPDATE products SET name={product_data} WHERE id={id}")
    conn.commit()
    return {"message": "Product updated"}

@app.delete("/product/{id}")
async def delete_product(id: int):
    c.execute(f"DELETE FROM products WHERE id={id}")
    conn.commit()
    return {"message": "Product deleted"}