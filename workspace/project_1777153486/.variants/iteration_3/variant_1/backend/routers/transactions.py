from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit", response_model=TransactionResponse)
def deposit(transaction: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == transaction.receiver).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    new_transaction = Transaction(sender=None, receiver=account.account_number, amount=transaction.amount)
    db.add(new_transaction)
    
    account.balance += transaction.amount
    db.commit()
    return new_transaction

@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(transaction: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == transaction.sender).first()
    
    if not account or account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    new_transaction = Transaction(sender=account.account_number, receiver=None, amount=transaction.amount)
    db.add(new_transaction)
    
    account.balance -= transaction.amount
    db.commit()
    return new_transaction

@router.post("/transfer", response_model=TransactionResponse)
def transfer(transaction: TransactionCreate, db: Session = Depends(get_db)):
    sender_account = db.query(Account).filter(Account.account_number == transaction.sender).first()
    
    if not sender_account or sender_account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    receiver_account = db.query(Account).filter(Account.account_number == transaction.receiver).first()
    
    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver account does not exist")
        
    new_transaction = Transaction(sender=sender_account.account_number, receiver=receiver_account.account_number, amount=transaction.amount)
    db.add(new_transaction)
    
    sender_account.balance -= transaction.amount
    receiver_account.balance += transaction.amount
    db.commit()
    return new_transaction