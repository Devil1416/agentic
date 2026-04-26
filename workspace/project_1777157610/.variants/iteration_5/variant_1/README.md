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

### Dependencies

- fastapi
- uvicorn
- sqlalchemy
- pydantic
- python-dotenv
- react
- vite

## Files

| Path | Purpose |
| ---- | ------- |
| api/database.py | Handles the SQLAlchemy engine and session creation for the SQLite database. |
| api/models.py | Defines the SQLAlchemy ORM model for the Product entity. |
| api/schemas.py | Defines Pydantic schemas for request/response validation (e.g., ProductCreate, ProductResponse). |
| api/main.py | The main FastAPI application entry point, containing the router and CRUD endpoints. |
| web/src/App.jsx | The main React component that fetches and displays the product list. |
| web/src/components/ProductList.jsx | A reusable component to render the list of products. |
| web/src/api/productService.js | Utility functions for making API calls to the FastAPI backend. |
| setup.sh | A shell script to set up the environment, install dependencies, and run the application. |
| README.md | Project documentation, setup instructions, and usage guide. |

## Setup Instructions

1. Clone this repository: `git clone https://github.com/your-repo-url`
2. Navigate to your project directory: `cd your-project-directory`
3. Install the dependencies: `sh setup.sh`
4. Run the application: `uvicorn api.main:app --reload` and `npm run dev` in separate terminals
5. Open a web browser and navigate to http://localhost:5173 to view the frontend.

## Usage Guide

The E-commerce Platform allows users to perform CRUD operations on products. 

### Create Product

To create a new product, send a POST request to `http://localhost:8000/products` with a JSON body containing the product details (name, description, price).

Example:
```json
{
    "name": "Product Name",
    "description": "Product Description",
    "price": 123.45
}
```

### Read Products

To view a list of all products, send a GET request to `http://localhost:8000/products`.

### Update Product

To update an existing product, send a PUT or PATCH request to `http://localhost:8000/products/{product_id}` with a JSON body containing the updated details (name, description, price).

Example:
```json
{
    "name": "Updated Product Name",
    "description": "Updated Product Description",
    "price": 543.21
}
```

### Delete Product

To delete a product, send a DELETE request to `http://localhost:8000/products/{product_id}`.

## Testing

You can test the API endpoints using tools like Postman or curl. For frontend testing, you can use libraries like Jest and React Testing Library.