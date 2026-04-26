from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import TransactionSchema, DepositSchema, WithdrawSchema, TransferSchema

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit")
async def deposit(data: DepositSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Sender's account does not exist")
        
    account.balance += data.amount
    db.commit()
    
    transaction = Transaction(**data.dict(), timestamp=datetime.utcnow())
    db.add(transaction)
    db.commit()
    
    return {"detail": "Deposit successful"}

@router.post("/withdraw")
async def withdraw(data: WithdrawSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not account or account.balance < data.amount:
        raise HTTPException(status_code=404, detail="Insufficient balance")
        
    account.balance -= data.amount
    db.commit()
    
    transaction = Transaction(**data.dict(), timestamp=datetime.utcnow())
    db.add(transaction)
    db.commit()
    
    return {"detail": "Withdrawal successful"}

@router.post("/transfer")
async def transfer(data: TransferSchema, db: Session = Depends(get_db)):
    sender = db.query(Account).filter(Account.account_number == data.sender).first()
    
    if not sender or sender.balance < data.amount:
        raise HTTPException(status_code=404, detail="Insufficient balance")
        
    receiver = db.query(Account).filter(Account.account_number == data.receiver).first()
    
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver's account does not exist")
        
    sender.balance -= data.amount
    receiver.balance += data.amount
    db.commit()
    
    transaction = Transaction(**data.dict(), timestamp=datetime.utcnow())
    db.add(transaction)
    db.commit()
    
    return {"detail": "Transfer successful"}