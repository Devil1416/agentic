from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

DATABASE_NAME = "database.db"
TABLE_NAME = "products"

@app.on_event("startup")
async def startup():
    app.state.conn = sqlite3.connect(DATABASE_NAME)
    cursor = app.state.conn.cursor()
    cursor.execute(f'CREATE TABLE IF NOT EXISTS {TABLE_NAME} (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL);')
    cursor.close()

@app.on_event("shutdown")
async def shutdown():
    app.state.conn.close()

@app.get("/products/")
def read_all_products():
    cursor = app.state.conn.cursor()
    rows = cursor.execute(f'SELECT * FROM {TABLE_NAME};').fetchall()
    products = [models.Product(*row) for row in rows]
    cursor.close()
    return {"data": products}

@app.get("/products/{product_id}/")
def read_product(product_id: int):
    cursor = app.state.conn.cursor()
    row = cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id=?;', (product_id,)).fetchone()
    product = models.Product(*row) if row else None
    cursor.close()
    return {"data": product}

@app.post("/products/")
def create_product(product: models.Product):
    cursor = app.state.conn.cursor()
    cursor.execute(f'INSERT INTO {TABLE_NAME} (name, description, price) VALUES (?, ?, ?);', 
                   (product.name, product.description, product.price))
    app.state.conn.commit()
    cursor.close()
    return {"data": "Product created"}

@app.put("/products/{product_id}/")
def update_product(product_id: int, product: models.Product):
    cursor = app.state.conn.cursor()
    cursor.execute(f'UPDATE {TABLE_NAME} SET name=?, description=?, price=? WHERE id=?;', 
                   (product.name, product.description, product.price, product_id))
    app.state.conn.commit()
    cursor.close()
    return {"data": "Product updated"}

@app.delete("/products/{product_id}/")
def delete_product(product_id: int):
    cursor = app.state.conn.cursor()
    cursor.execute(f'DELETE FROM {TABLE_NAME} WHERE id=?;', (product_id,))
    app.state.conn.commit()
    cursor.close()
    return {"data": "Product deleted"}