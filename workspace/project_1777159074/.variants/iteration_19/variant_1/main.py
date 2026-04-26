from fastapi import FastAPI
import sqlite3

app = FastAPI()

# Connect to SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/products/")
async def create_product(name: str, description: str, price: float):
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    conn.commit()
    return {"status": "Product created"}

@app.get("/products/")
async def read_products():
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    return rows

@app.put("/products/{product_id}")
async def update_product(product_id: int, name: str, description: str, price: float):
    c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", (name, description, price, product_id))
    conn.commit()
    return {"status": "Product updated"}

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    return {"status": "Product deleted"}