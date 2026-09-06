from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.models.feedback import Feedback

router = APIRouter()


class FeedbackRequest(BaseModel):
    report: str
    products_summary: str = ""
    product_count: int = 0
    satisfaction: bool
    comment: str = ""


@router.post("")
def submit_feedback(
    req: FeedbackRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户提交批量分析反馈，存库供管理员查看。"""
    if not req.report.strip():
        raise HTTPException(400, "报告内容不能为空")
    fb = Feedback(
        user_id=current.id,
        user_account=current.username,
        user_nickname=getattr(current, "nickname", None) or current.username,
        report=req.report,
        products_summary=req.products_summary,
        product_count=req.product_count,
        satisfaction=req.satisfaction,
        comment=req.comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {"ok": True, "id": fb.id}
