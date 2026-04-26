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
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer, index=True)
```

### api/schemas.py
Defines Pydantic schemas for request/response validation (e.g., ProductCreate, ProductResponse).

```python
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True
```

### api/main.py
The main FastAPI application entry point, containing the router and CRUD endpoints.

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import crud, schemas, database

app = FastAPI()
database.Base.metadata.create_all(bind=database.engine)  # Create tables if not exist

def get_db():
    db = None
    try:
        yield db
    finally:
        db.close()

@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db=db, product=product)

@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    return crud.read_product(db=db, product_id=product_id)

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.update_product(db=db, product_id=product_id, product=product)

@app.delete("/products/{product_id}", response_model=schemas.Product)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    return crud.delete_product(db=db, product_id=product_id)
```

### web/src/App.jsx
The main React component that fetches and displays the product list.

```javascript
import React from 'react';
import ProductList from './components/ProductList';
import { getProducts } from './api/productService';

class App extends React.Component {
  state = { products: [] };

  async componentDidMount() {
    const products = await getProducts();
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

export function getProducts() {
  return axios.get(apiUrl).then(response => response.data);
}
```

### setup.sh
A shell script to set up the environment, install dependencies, and run the application.

```bash
#!/bin/bash

# Install Python dependencies (FastAPI, SQLAlchemy)
pip install fastapi[all] sqlalchemy pydantic python-dotenv uvicorn

# Initialize the SQLite database and create tables
python api/database.py

# Run the FastAPI backend server
uvicorn api.main:app --reload

# Install JavaScript dependencies (React, Vite)
npm install react vite

# Run the React development server
cd web && npm run dev
```