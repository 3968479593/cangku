from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.models.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, comment="商品名称")
    category = Column(String(200), comment="品类")
    price = Column(Float, comment="价格")
    platform = Column(String(100), comment="平台来源")
    sales_volume = Column(Integer, default=0, comment="销量")
    rating = Column(Float, default=0, comment="评分")
    description = Column(Text, comment="商品描述")
    source_doc = Column(String(500), comment="来源文档")
    chroma_dense_id = Column(String(200), comment="稠密向量Chroma ID")
    chroma_sparse_id = Column(String(200), comment="稀疏向量Chroma ID")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
