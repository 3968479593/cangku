from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.models.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False, comment="原始文件名")
    file_path = Column(String(1000), comment="存储路径")
    file_type = Column(String(50), comment="文件类型 pdf/csv/xlsx")
    status = Column(String(20), default="pending", comment="处理状态")
    chunk_count = Column(Integer, default=0, comment="切片数量")
    created_at = Column(DateTime, server_default=func.now())


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False, comment="所属文档ID")
    chunk_index = Column(Integer, nullable=False, comment="切片序号")
    content = Column(Text, nullable=False, comment="切片文本内容")
    token_count = Column(Integer, default=0, comment="token数")
    chroma_dense_id = Column(String(200), comment="稠密向量Chroma ID")
    chroma_sparse_id = Column(String(200), comment="稀疏向量Chroma ID")
    created_at = Column(DateTime, server_default=func.now())
