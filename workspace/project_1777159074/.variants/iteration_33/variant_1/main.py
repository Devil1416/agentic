from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import sqlite3
from typing import List

app = FastAPI()

@app.get("/products")
async def read_products():
    conn = sqlite3.connect("e-commerce_app.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    conn.close()
    return JSONResponse(content={"products": rows}, media_type="application/json")