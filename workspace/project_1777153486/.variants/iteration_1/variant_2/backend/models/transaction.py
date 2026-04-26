from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, ForeignKey("accounts.id"))
    receiver = Column(String, ForeignKey("accounts.id"))
    amount = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    sender_account = relationship("Account", foreign_keys=[sender])
    receiver_account = relationship("Account", foreign_keys=[receiver])