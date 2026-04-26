from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction_schema import DepositSchema, WithdrawSchema, TransferSchema

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/deposit")
async def deposit(request: DepositSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == request.account_number).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    account.balance += request.amount
    new_transaction = Transaction(sender=None, receiver=account.account_number, amount=request.amount)
    
    db.add(new_transaction)
    db.commit()
    
    return {"detail": "Deposit successful", "balance": account.balance}

@router.post("/withdraw")
async def withdraw(request: WithdrawSchema, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == request.account_number).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if account.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    account.balance -= request.amount
    new_transaction = Transaction(sender=account.account_number, receiver=None, amount=request.amount)
    
    db.add(new_transaction)
    db.commit()
    
    return {"detail": "Withdrawal successful", "balance": account.balance}

@router.post("/transfer")
async def transfer(request: TransferSchema, db: Session = Depends(get_db)):
    sender = db.query(Account).filter(Account.account_number == request.sender_account_number).first()
    
    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found")
        
    receiver = db.query(Account).filter(Account.account_number == request.receiver_account_number).first()
    
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")
        
    if sender.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    sender.balance -= request.amount
    receiver.balance += request.amount
    
    new_transaction = Transaction(sender=request.sender_account_number, receiver=request.receiver_account_number, amount=request.amount)
    
    db.add(new_transaction)
    db.commit()
    
    return {"detail": "Transfer successful", "balance": sender.balance}