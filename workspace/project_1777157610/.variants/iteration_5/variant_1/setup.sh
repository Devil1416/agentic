Here is a basic setup script for your project. It assumes that you have Node.js, npm, Python, pip installed on your system and it's being run in the root directory of your project. 

```bash
#!/bin/sh

# Install backend dependencies
echo "Installing backend dependencies..."
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# Initialize SQLite database and create tables
echo "Initializing the SQLite database and creating tables..."
python api/database.py

# Run FastAPI server in background
echo "Running FastAPI server..."
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &

# Install frontend dependencies
cd web || exit
npm install react vite

# Run React development server
echo "Running React development server..."
npx vite
```

This script is a simple setup for your project. It assumes that you have Node.js, npm, Python, pip installed on your system and it's being run in the root directory of your project. 

Please note that this script doesn't handle errors or edge cases. You might need to modify it according to your needs. Also, make sure to replace `api/database.py` with the correct path to your database setup file if it's different.