from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Account(Base):
    __tablename__ = "accounts"
    
    account_number = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=0.0)
    owner_id = Column(String, ForeignKey("users.username"))

    owner = relationship("User", back_populates="accounts")