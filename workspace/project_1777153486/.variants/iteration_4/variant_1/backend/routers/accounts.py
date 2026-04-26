from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..schemas.account_schema import AccountBase, AccountOut
from ..auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/open", response_model=AccountOut)
def open_account(
    account: AccountBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User is not authenticated")
    
    account_data = account.dict()
    account_data["owner_id"] = current_user.id
    new_account = Account(**account_data)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account

@router.get("/balance", response_model=List[AccountOut])
def view_balances(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User is not authenticated")
    
    accounts = db.query(Account).filter(Account.owner_id == current_user.id).all()
    
    return accounts