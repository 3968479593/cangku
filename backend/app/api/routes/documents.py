import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import get_db
from app.models.document import Document
from app.models.schemas import DocumentOut
from app.core.document_processor import process_document
from app.api.deps import get_ingestion_service
from app.models.product import Product
from app.core.vector_store import delete_from_chroma
from app.services.product_import import is_product_file, import_products_from_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
):
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in ("pdf", "csv", "xlsx", "xls", "txt"):
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    save_name = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_name)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"文件大小超过 {settings.MAX_UPLOAD_SIZE_MB}MB 限制")

    with open(save_path, "wb") as f:
        f.write(content)

    # ---- 自动检测：商品数据文件走商品导入管道 ----
    if ext in ("csv", "xlsx", "xls") and is_product_file(save_path):
        try:
            product_count = import_products_from_file(save_path, db)
            # 在文档列表留一条记录，便于管理员查看商品导入历史
            doc = Document(
                filename=file.filename,
                file_path=save_path,
                file_type=ext,
                status="completed",
                chunk_count=product_count,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return {
                "type": "product_import",
                "filename": file.filename,
                "file_type": ext,
                "status": "completed",
                "product_count": product_count,
                "message": f"商品数据导入成功，共 {product_count} 条",
            }
        except Exception as e:
            logger.exception("商品导入失败: %s", file.filename)
            raise HTTPException(500, f"商品导入失败: {str(e)}")

    # ---- 普通文档走 RAG 切片管道 ----
    doc = Document(
        filename=file.filename,
        file_path=save_path,
        file_type=ext,
        status="uploaded",
        chunk_count=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        doc.status = "processing"
        db.commit()

        chunks = process_document(save_path, ext)
        chunk_count = ingestion_service.ingest_chunks(chunks, doc.id, db)
        doc.chunk_count = chunk_count
        doc.status = "completed"
        db.commit()
        db.refresh(doc)
    except Exception as e:
        logger.exception("文档处理失败: %s", file.filename)
        doc.status = "failed"
        db.commit()
        raise HTTPException(500, f"文档处理失败: {str(e)}")

    return doc


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Document)
    if status:
        q = q.filter(Document.status == status)
    return q.order_by(Document.created_at.desc()).all()


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "文档不存在")

    # 联动删除：商品导入文档 → 清理对应 products + Chroma 向量
    source_doc = os.path.basename(doc.file_path or "")
    deleted_products = 0
    if source_doc:
        products = db.query(Product).filter(Product.source_doc == source_doc).all()
        chroma_ids = [p.chroma_dense_id for p in products if p.chroma_dense_id]
        if chroma_ids:
            try:
                delete_from_chroma(chroma_ids)
            except Exception as e:
                logger.warning("Chroma 向量删除失败: %s", e)
        for p in products:
            db.delete(p)
        deleted_products = len(products)

    # 删除物理文件
    try:
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        logger.warning("物理文件删除失败: %s", e)

    db.delete(doc)
    db.commit()
    return {"message": "删除成功", "deleted_products": deleted_products}
