from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from sqlalchemy.sql import func

from app.models.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="管理员账号")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 哈希")
    role = Column(String(50), nullable=False, default="admin", comment="角色")
    is_active = Column(SmallInteger, nullable=False, default=1, comment="是否启用 1/0")
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True, comment="最近登录时间")
