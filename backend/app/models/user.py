from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 哈希")
    nickname = Column(String(50), nullable=False, comment="昵称")
    created_at = Column(DateTime, server_default=func.now())
