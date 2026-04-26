from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    accounts = relationship("Account", back_populates="owner")

    def verify_password(self, password):
        return pwd_context.verify(password, self.hashed_password)

    @classmethod
    def get_user(cls, db, username: str):
        return db.query(User).filter(User.username == username).first()

    @classmethod
    def authenticate_user(cls, db, username: str, password: str):
        user = cls.get_user(db, username)
        if not user:
            return False
        return user.verify_password(password)