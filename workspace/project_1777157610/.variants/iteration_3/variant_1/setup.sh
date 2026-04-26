Here is a basic setup script for your project. This script assumes that you have Node.js (npm), Python (pip), and SQLite installed on your system. It also assumes that the FastAPI backend server runs at http://localhost:8000, which might need to be adjusted based on your actual setup.

```bash
#!/bin/bash
set -e

# Install dependencies
echo "Installing Python dependencies..."
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

echo "Installing Node.js dependencies..."
npm install react vite

# Initialize the SQLite database and create tables
echo "Initializing the SQLite database and creating tables..."
python api/database.py

# Run the FastAPI backend server in a separate terminal window
echo "Running the FastAPI backend server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Wait for the FastAPI server to start
sleep 5

# Run the React development server in a separate terminal window
echo "Running the React development server..."
cd web && npm run dev &
```

Please note that this is a very basic setup script and might need adjustments based on your specific project requirements. It also assumes that you have already set up the FastAPI backend, SQLAlchemy models, Pydantic schemas, and React frontend as per your project plan.