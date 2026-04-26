from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import TransactionSchema, TransactionResponse
from .auth import verify_token

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit", response_model=TransactionResponse)
async def deposit(data: TransactionSchema, db: Session = Depends(get_db), user: str = Depends(verify_token)):
    account = db.query(Account).filter(Account.account_number == data.receiver).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    new_balance = account.balance + data.amount
    account.balance = new_balance
    
    db.commit()
    db.refresh(account)
    
    transaction = Transaction(sender=None, receiver=data.receiver, amount=data.amount)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {"message": "Deposit successful", "account_balance": new_balance}

@router.post("/withdraw", response_model=TransactionResponse)
async def withdraw(data: TransactionSchema, db: Session = Depends(get_db), user: str = Depends(verify_token)):
    account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not account or account.balance < data.amount:
        raise HTTPException(status_code=403, detail="Insufficient balance")
        
    new_balance = account.balance - data.amount
    account.balance = new_balance
    
    db.commit()
    db.refresh(account)
    
    transaction = Transaction(sender=data.sender, receiver=None, amount=data.amount)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {"message": "Withdrawal successful", "account_balance": new_balance}

@router.post("/transfer", response_model=TransactionResponse)
async def transfer(data: TransactionSchema, db: Session = Depends(get_db), user: str = Depends(verify_token)):
    sender_account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not sender_account or sender_account.balance < data.amount:
        raise HTTPException(status_code=403, detail="Insufficient balance")
        
    receiver_account = db.query(Account).filter(Account.account_number == data.receiver).first()
    
    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    sender_new_balance = sender_account.balance - data.amount
    sender_account.balance = sender_new_balance
    
    receiver_new_balance = receiver_account.balance + data.amount
    receiver_account.balance = receiver_new_balance
    
    db.commit()
    db.refresh(sender_account)
    db.refresh(receiver_account)
    
    sender_transaction = Transaction(sender=data.sender, receiver=None, amount=data.amount)
    db.add(sender_transaction)
    db.commit()
    db.refresh(sender_transaction)
    
    receiver_transaction = Transaction(sender=None, receiver=data.receiver, amount=data.amount)
    db.add(receiver_transaction)
    db.commit()
    db.refresh(receiver_transaction)
    
    return {"message": "Transfer successful", "account_balance": sender_new_balance}