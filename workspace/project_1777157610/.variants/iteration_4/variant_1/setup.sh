Here is a basic setup script for your project. This script assumes that you have Node.js, npm, Python, pip installed on your system and it will install the dependencies using those tools. It also starts both backend (FastAPI server) and frontend (React development server). Please adjust this script according to your needs:

```bash
#!/bin/bash
set -e

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# Initialize the SQLite database and create tables
python api/database.py

# Run the FastAPI backend server in background
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &

# Navigate to frontend directory and install dependencies using npm
cd web
npm install react vite
npx vite build
nohup npm run dev --host > /dev/null 2>&1 &
```

Please note that this is a very basic setup script. It doesn't cover all possible error cases or edge conditions, and it might not work perfectly for your project. You may need to modify or extend it according to your specific requirements. Also, remember to replace the file paths in the script with the correct ones based on your project structure.