from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import sqlite3
import uvicorn

app = FastAPI()

@app.get("/products/")
async def read_products():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    conn.close()
    return JSONResponse(content={"products": rows}, media_type="application/json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)