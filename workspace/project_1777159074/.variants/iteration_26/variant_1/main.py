from fastapi import FastAPI
import uvicorn
from api.models import Product

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/products/", response_model=Product)
async def create_product(product: Product):
    # Insert product into database here
    pass

@app.get("/products/{item_id}", response_model=Product)
async def read_product(item_id: str):
    # Fetch product from database here
    pass

@app.put("/products/{item_id}", response_model=Product)
async def update_product(item_id: str, product: Product):
    # Update product in the database here
    pass

@app.delete("/products/{item_id}")
async def delete_product(item_id: str):
    # Delete product from the database here
    pass

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")