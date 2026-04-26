# README.md

## E-commerce Platform
A full-stack e-commerce application allowing users to view product listings and providing a robust backend for product management (CRUD).

## Architecture
Client-Server architecture using a REST API. The React frontend communicates with the FastAPI backend, which interacts with a shared SQLite database.

## Language
Python/JavaScript

## Dependencies
fastapi, uvicorn, sqlalchemy, pydantic, python-dotenv, react, vite

## Files
### api/database.py
Handles the SQLAlchemy engine and session creation for the SQLite database.

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

### api/models.py
Defines the SQLAlchemy ORM model for the Product entity.

```python
from sqlalchemy import Column, Integer, String
from .database import Base

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Float)
```

### api/schemas.py
Defines Pydantic schemas for request/response validation (e.g., ProductCreate, ProductResponse).

```python
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: int

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
```

### api/main.py
The main FastAPI application entry point, containing the router and CRUD endpoints.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, schemas, database

router = APIRouter()

# Dependency
def get_db():
    db = None
    try:
        yield db
    finally:
        db.close()

@router.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db=db, product=product)

@router.get("/products/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db=db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = crud.update_product(db=db, product=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.delete("/products/{product_id}", response_model=schemas.ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.delete_product(db=db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product
```

### web/src/App.jsx
The main React component that fetches and displays the product list.

```javascript
import React from 'react';
import ProductList from './components/ProductList';
import { getAllProducts } from './api/productService';

class App extends React.Component {
  state = { products: [] };

  async componentDidMount() {
    const products = await getAllProducts();
    this.setState({ products });
  }

  render() {
    return (
      <div className="App">
        <h1>E-commerce Platform</h1>
        {this.state.products && <ProductList products={this.state.products} />}
      </div>
    );
  }
}

export default App;
```

### web/src/components/ProductList.jsx
A reusable component to render the list of products.

```javascript
import React from 'react';

const ProductList = ({ products }) => {
  return (
    <ul>
      {products.map(product => (
        <li key={product.id}>
          <h2>{product.name}</h2>
          <p>{product.description}</p>
          <p>${product.price}</p>
        </li>
      ))}
    </ul>
  );
};

export default ProductList;
```

### web/src/api/productService.js
Utility functions for making API calls to the FastAPI backend.

```javascript
import axios from 'axios';

const apiUrl = '/products';

export const getAllProducts = async () => {
  try {
    const response = await axios.get(apiUrl);
    return response.data;
  } catch (error) {
    console.log('Error fetching products: ', error);
  }
};
```

### setup.sh
A shell script to set up the environment, install dependencies, and run the application.

```bash
#!/bin/bash

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# Initialize the SQLite database and create tables
python -m api.database

# Run the FastAPI backend server
uvicorn api.main:app --reload

# Run the React development server
cd web && npm install && npm run dev
```