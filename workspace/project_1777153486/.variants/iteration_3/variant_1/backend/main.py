from fastapi import FastAPI
from backend.routers import auth, accounts, transactions

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)