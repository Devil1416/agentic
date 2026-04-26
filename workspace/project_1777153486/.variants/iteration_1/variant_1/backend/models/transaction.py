from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, ForeignKey("accounts.account_number"))
    receiver = Column(String, ForeignKey("accounts.account_number"))
    amount = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)