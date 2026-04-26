from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit", response_model=TransactionResponse)
def deposit(request: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == request.sender).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Sender account does not exist")
        
    transaction = Transaction(sender=request.sender, receiver=None, amount=request.amount)
    db.add(transaction)
    
    account.balance += request.amount
    db.commit()
    db.refresh(account)
    
    return {"sender": transaction.sender, "receiver": transaction.receiver, "amount": transaction.amount}

@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(request: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == request.sender).first()
    
    if not account or account.balance < request.amount:
        raise HTTPException(status_code=404, detail="Insufficient balance")
        
    transaction = Transaction(sender=request.sender, receiver=None, amount=-request.amount)
    db.add(transaction)
    
    account.balance -= request.amount
    db.commit()
    db.refresh(account)
    
    return {"sender": transaction.sender, "receiver": transaction.receiver, "amount": transaction.amount}

@router.post("/transfer", response_model=TransactionResponse)
def transfer(request: TransactionCreate, db: Session = Depends(get_db)):
    sender_account = db.query(Account).filter(Account.account_number == request.sender).first()
    
    if not sender_account or sender_account.balance < request.amount:
        raise HTTPException(status_code=404, detail="Insufficient balance")
        
    receiver_account = db.query(Account).filter(Account.account_number == request.receiver).first()
    
    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    transaction1 = Transaction(sender=request.sender, receiver=request.receiver, amount=-request.amount)
    db.add(transaction1)
    
    sender_account.balance -= request.amount
    db.commit()
    db.refresh(sender_account)
    
    transaction2 = Transaction(sender=None, receiver=request.receiver, amount=request.amount)
    db.add(transaction2)
    
    receiver_account.balance += request.amount
    db.commit()
    db.refresh(receiver_account)
    
    return {"sender": transaction1.sender, "receiver": transaction1.receiver, "amount": transaction1.amount}