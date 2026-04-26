from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import TransactionSchema, TransactionResponseSchema

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit", response_model=TransactionResponseSchema)
def deposit(data: TransactionSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == data.receiver).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    transaction = Transaction(sender=None, receiver=data.receiver, amount=data.amount)
    db.add(transaction)
    
    account.balance += data.amount
    db.commit()
    return transaction

@router.post("/withdraw", response_model=TransactionResponseSchema)
def withdraw(data: TransactionSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not account or account.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    transaction = Transaction(sender=data.sender, receiver=None, amount=-data.amount)
    db.add(transaction)
    
    account.balance -= data.amount
    db.commit()
    return transaction

@router.post("/transfer", response_model=TransactionResponseSchema)
def transfer(data: TransactionSchema, db: Session = Depends(get_db)):
    sender_account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not sender_account or sender_account.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    receiver_account = db.query(Account).filter(Account.account_number == data.receiver).first()
    
    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    sender_transaction = Transaction(sender=data.sender, receiver=data.receiver, amount=-data.amount)
    db.add(sender_transaction)
    
    receiver_transaction = Transaction(sender=None, receiver=data.receiver, amount=data.amount)
    db.add(receiver_transaction)
    
    sender_account.balance -= data.amount
    receiver_account.balance += data.amount
    db.commit()
    return sender_transaction