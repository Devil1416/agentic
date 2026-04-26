#!/bin/bash

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# Initialize the SQLite database and create tables
python api/database.py

# Run the FastAPI backend server
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Install React dependencies
npm install react vite

# Build the frontend
cd web && npm run build

# Run the React development server
vite serve dist/index.html --host 0.0.0.0 --port 5173 &
```
This script should be saved as `setup.sh` in your project root directory and made executable using `chmod +x setup.sh`. It installs the necessary Python dependencies, initializes the SQLite database and creates tables, runs the FastAPI backend server on port 8000, installs React dependencies, builds the frontend, and runs the development server on port 5173.