from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_banned = Column(Boolean, default=False)
    mute_until = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username})>"
