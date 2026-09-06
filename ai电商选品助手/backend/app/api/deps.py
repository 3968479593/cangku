from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_token
from app.core.vector_store import get_dense_collection
from app.models.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.services.ingestion import IngestionService

# tokenUrl 仅用于 OpenAPI 文档展示，不影响实际登录接口路径
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """校验 Bearer Token，返回当前登录用户；管理员 token 也可访问用户端接口。"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的登录凭证")

    # 管理员 token：查 admins 表返回 Admin 对象（鸭子类型兼容 User 的使用场景）
    if payload.get("role") == "admin":
        admin = db.query(Admin).filter(Admin.id == int(user_id)).first()
        if not admin:
            raise HTTPException(status_code=401, detail="管理员不存在")
        return admin

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    """校验管理员 Bearer Token，返回当前管理员；非管理员或失败返回 401。"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")
    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(status_code=401, detail="无效的登录凭证")

    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    if not admin:
        raise HTTPException(status_code=401, detail="管理员不存在")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="管理员账号已被禁用")
    return admin
