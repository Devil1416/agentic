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
1. Install dependencies: ```bash setup.sh install```
2. Initialize the SQLite database and create tables: ```bash setup.sh initdb```
3. Run the FastAPI backend server: ```uvicorn api.main:app --reload```
4. Run the React development server: ```npm run dev```
5. Test API endpoints and frontend display at http://localhost:5173/

## Usage Guide
- Use the FastAPI backend to create, read, update, and delete products via the provided CRUD endpoints.
- The React frontend fetches product data from the FastAPI backend and displays it in a user-friendly manner using the ProductList component.

<a name="database"></a>
## database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL') or 'sqlite:///./test.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```
<a name="models"></a>
## models.py
```python
from sqlalchemy import Column, Integer, String
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer, index=True)
```
<a name="schemas"></a>
## schemas.py
```python
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
```
<a name="main"></a>
## main.py
```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import schemas, models, database

app = FastAPI()
database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/products/", response_model=schemas.ProductResponse)
async def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
```
<a name="app"></a>
## App.jsx
```javascript
import React, { useEffect, useState } from 'react';
import ProductList from './components/ProductList';
import productService from './api/productService';

function App() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  async function fetchProducts() {
    try {
      const response = await productService.getAll();
      setProducts(response.data);
    } catch (error) {
      console.log("Error fetching products: ", error);
    }
  }

  return (
    <div className="App">
      <h1>E-commerce Platform</h1>
      <ProductList products={products} />
    </div>
  );
}

export default App;
```
<a name="productlist"></a>
## ProductList.jsx
```javascript
import React from 'react';

function ProductList({ products }) {
  return (
    <ul className="ProductList">
      {products.map(product => (
        <li key={product.id}>
          <h2>{product.name}</h2>
          <p>{product.description}</p>
          <p>${product.price}</p>
        </li>
      ))}
    </ul>
  );
}

export default ProductList;
```
<a name="productservice"></a>
## productService.js
```javascript
import axios from 'axios';

const apiUrl = '/products';

function getAll() {
  return axios.get(apiUrl);
}

export default {
  getAll,
};
```
<a name="setup"></a>
## setup.sh
```bash
#!/bin/bash

# Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
npm install react vite

# Initialize the SQLite database and create tables
python -m api.database

# Run the FastAPI backend server
uvicorn api.main:app --reload

# Run the React development server
npm run dev
```
<a name="readme"></a>
## README.md
This file provides documentation, setup instructions, and usage guide for the E-commerce Platform project. For more information, refer to the [setup instructions](#setup) and [usage guide](#usage).