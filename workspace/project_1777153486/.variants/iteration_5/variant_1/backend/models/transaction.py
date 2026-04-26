from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, ForeignKey("accounts.account_number"))
    receiver = Column(String, ForeignKey("accounts.account_number"))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    sender_account = relationship("Account", foreign_keys=[sender])
    receiver_account = relationship("Account", foreign_keys=[receiver])