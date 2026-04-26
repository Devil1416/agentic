from fastapi import FastAPI
import sqlite3
from .models import Product

app = FastAPI()

# Connect to SQLite database
conn = sqlite3.connect('products.db')
c = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/product/", response_model=Product)
async def create_product(product: Product):
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
              (product.name, product.description, product.price))
    conn.commit()
    return product

@app.get("/products/", response_model=List[Product])
async def read_products():
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    products = []
    for row in rows:
        product = Product(id=row[0], name=row[1], description=row[2], price=row[3])
        products.append(product)
    return products

@app.put("/product/{item_id}", response_model=Product)
async def update_product(item_id: int, product: Product):
    c.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?", 
              (product.name, product.description, product.price, item_id))
    conn.commit()
    return product

@app.delete("/product/{item_id}")
async def delete_product(item_id: int):
    c.execute("DELETE FROM products WHERE id = ?", (item_id,))
    conn.commit()
    return {"detail": f"Product {item_id} deleted"}