import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import create_admin_token, verify_password
from app.models.admin import Admin
from app.models.database import get_db
from app.models.schemas import AdminOut, AdminLoginRequest, AdminTokenResponse
from app.models.feedback import Feedback

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=AdminTokenResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """管理员登录，返回带 role=admin 的 JWT。"""
    admin = db.query(Admin).filter(Admin.username == req.username.strip()).first()
    if not admin:
        raise HTTPException(401, "管理员账号不存在")
    if not admin.is_active:
        raise HTTPException(403, "管理员账号已被禁用")
    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(401, "密码错误")

    admin.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(admin)

    token = create_admin_token(admin.id, admin.username)
    return AdminTokenResponse(access_token=token, admin=AdminOut.model_validate(admin))


@router.get("/me", response_model=AdminOut)
def admin_me(current: Admin = Depends(get_current_admin)):
    """获取当前登录管理员信息。"""
    return current


@router.get("/feedback")
def list_feedback(current: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """管理员查看所有用户对批量分析的反馈 + 统计。"""
    total = db.query(Feedback).count()
    satisfied = db.query(Feedback).filter(Feedback.satisfaction.is_(True)).count()
    unsatisfied = db.query(Feedback).filter(Feedback.satisfaction.is_(False)).count()
    items = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
    return {
        "total": total,
        "satisfied": satisfied,
        "unsatisfied": unsatisfied,
        "satisfaction_rate": round(satisfied / total * 100, 1) if total else 0,
        "items": [
            {
                "id": f.id,
                "user_account": f.user_account,
                "user_nickname": f.user_nickname,
                "satisfaction": f.satisfaction,
                "comment": f.comment,
                "product_count": f.product_count,
                "products_summary": f.products_summary,
                "report": f.report,
                "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else None,
            }
            for f in items
        ],
    }


@router.delete("/feedback/{fb_id}")
def delete_feedback(fb_id: int, current: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """管理员删除一条用户反馈。"""
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(404, "反馈不存在")
    db.delete(fb)
    db.commit()
    return {"ok": True}
