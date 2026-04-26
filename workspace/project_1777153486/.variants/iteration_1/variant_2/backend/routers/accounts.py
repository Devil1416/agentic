from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.account import Account
from ..schemas.account_schema import AccountBase, AccountOut
from ..auth import get_current_active_user

router = APIRouter()

@router.post("/open", response_model=AccountOut)
def open_account(
    account: AccountBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    db_account = db.query(Account).filter(Account.owner_id == current_user.id).first()
    if db_account:
        raise HTTPException(status_code=400, detail="User already has an account")
        
    new_account = Account(**account.dict(), owner_id=current_user.id)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account

@router.get("/balance", response_model=AccountOut)
def get_balance(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    account = db.query(Account).filter(Account.owner_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="User does not have an account")
        
    return account