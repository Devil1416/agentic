# README.md

## E-commerce Platform
A full-stack e-commerce application allowing users to view product listings and providing a robust backend for product management (CRUD).

### Architecture
Client-Server architecture using a REST API. The React frontend communicates with the FastAPI backend, which interacts with a shared SQLite database.

### Language
Python/JavaScript

### Frontend
React + Vite

### Backend
FastAPI

### Communication
REST

## Dependencies
- fastapi
- uvicorn
- sqlalchemy
- pydantic
- python-dotenv
- react
- vite

## Files
- [database.py](#database)
- [models.py](#models)
- [schemas.py](#schemas)
- [main.py](#main)
- [App.jsx](#app)
- [ProductList.jsx](#productlist)
- [productService.js](#productservice)
- [setup.sh](#setup)
- [README.md](#readme)

## Setup Instructions
1. Clone the repository: `git clone https://github.com/yourusername/ecommerce-platform.git`
2. Navigate to the project directory: `cd ecommerce-platform`
3. Install dependencies: `sh setup.sh`
4. Run the application: `sh setup.sh run`
5. Open your browser and navigate to http://localhost:8000 to view the application.

## Usage Guide
1. Use the navigation bar at the top of the page to switch between different product categories.
2. Click on a product to see more details about it, including its description, price, and image.
3. To add a new product, click on the "Add Product" button in the navigation bar. Fill out the form with the product's name, description, price, and image URL, then click "Submit".
4. You can edit or delete products by clicking on the corresponding buttons next to each product.

## Build Steps
1. Install Python dependencies (FastAPI, SQLAlchemy).
2. Initialize the SQLite database and create tables.
3. Run the FastAPI backend server.
4. Run the React development server.
5. Test API endpoints and frontend display.

## Subtasks
- Backend Setup and Database Initialization: [database.py](#database), [models.py](#models), [schemas.py](#schemas)
- Implement Product CRUD API: [main.py](#main)
- Frontend Setup and Product Display: [App.jsx](#app), [ProductList.jsx](#productlist), [productService.js](#productservice)
- Integration and Deployment Scripts: [setup.sh](#setup), [README.md](#readme)

## Workspace Directory
D:\\n1ggaman\\agentic\\workspace\\project_1777157610

### <a name="database"></a>database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL') or 'sqlite:///./test.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### <a<｜begin▁of▁sentence｜>name="models"></a>models.py
```python
from sqlalchemy import Column, Integer, String
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, index=True)
    image_url = Column(String, index=True)
```

### <a name="schemas"></a>schemas.py
```python
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
```

### <a name="main"></a>main.py
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db=db, product=product)

@app.get("/products/", response_model=List[schemas.ProductResponse])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db=db, skip=skip, limit=limit)
    return products

@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db=db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.get_product(db=db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.update_product(db=db, db_product=db_product, product=product)

@app.delete("/products/{product_id}", response_model=schemas.ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db=db, product_id=product_id)
    if db_product is None:<｜begin▁of▁sentence｜>name="app"></a>App.jsx
```javascript
import React from 'react';
import ProductList from './components/ProductList';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>E-commerce Platform</h1>
      </header>
      <main>
        <ProductList />
      </main>
    </div>
  );
}

export default App;
```

### <a name="productlist"></a>ProductList.jsx
```javascript
import React, { useState, useEffect } from 'react';
import ProductService from '../api/productService';

function ProductList() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  async function fetchProducts() {
    try {
      const response = await ProductService.getAll();
      setProducts(response.data);
    } catch (error) {
      console.log('Error fetching products: ', error);
    }
  }

  return (
    <div>
      <h2>Product List</h2>
      {products.map((product, index) => (
        <div key={index}>
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          <p>${product.price}</p>
          {product.image_url && <img src={product.image_url} alt={product.name} />}
        </div>
      ))}
    </div>
  );
}

export default ProductList;
```

### <a name="productservice"></a>productService.js
```javascript
import axios from 'axios';

const API_URL = 'http://localhost:8000/products';

class ProductService {
  getAll() {
    return axios.get(API_URL);
  }
}

export default new ProductService();
```

### <a name="setup"></a>setup.sh
```bash
#!/bin/bash

# Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
npm install react vite

# Initialize the SQLite database and create tables
python api/database.py

# Run the FastAPI backend server
uvicorn api.main:app --reload

# Run the React development server
cd web && npm run dev
```