from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.models.database import Base


class Feedback(Base):
    """用户对 AI 批量分析报告的反馈，供管理员查看分析。"""

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, comment="提交反馈的用户ID")
    user_account = Column(String(50), comment="用户账号（冗余便于管理员查看）")
    user_nickname = Column(String(50), comment="用户昵称（冗余）")
    report = Column(Text, comment="AI 批量分析报告快照")
    products_summary = Column(Text, comment="选定商品清单摘要")
    product_count = Column(Integer, default=0, comment="选定商品数量")
    satisfaction = Column(Boolean, nullable=False, comment="True=满意，False=不满意")
    comment = Column(Text, default="", comment="用户反馈意见")
    created_at = Column(DateTime, server_default=func.now())
