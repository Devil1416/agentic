from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.account import Account
from ..schemas.account_schema import AccountBase, AccountOut
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/open", response_model=AccountOut)
def open_account(
    account: AccountBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    new_account = Account(**account.dict(), owner_id=current_user.id)
    db.add(new_account)
    db.commit()
    return new_account

@router.get("/balance", response_model=List[AccountOut])
def view_balances(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    accounts = db.query(Account).filter(Account.owner_id == current_user.id).all()
    return accounts