from fastapi import FastAPI
import sqlite3
from . import models

app = FastAPI()

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

@app.get("/products")
def read_root():
    c.execute("SELECT * FROM products")
    return {"data": c.fetchall()}

@app.post("/product")
def create_item(item: models.Product):
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
              (item.name, item.description, item.price))
    conn.commit()
    return {"status": "success"}

@app.put("/product/{id}")
def update_item(id: int, item: models.Product):
    c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", 
              (item.name, item.description, item.price, id))
    conn.commit()
    return {"status": "success"}

@app.delete("/product/{id}")
def delete_item(id: int):
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return {"status": "success"}