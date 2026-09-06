import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.database import get_db
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户并直接返回登录态。"""
    username = req.username.strip()
    nickname = req.nickname.strip()
    if not username or not req.password or not nickname:
        raise HTTPException(400, "账号、密码、昵称不能为空")
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少 6 位")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "该账号已存在")

    user = User(
        username=username,
        password_hash=hash_password(req.password),
        nickname=nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """账号密码登录，返回 JWT。"""
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user:
        raise HTTPException(401, "账号不存在，请注册")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "密码错误")

    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current
