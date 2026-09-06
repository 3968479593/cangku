import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.document_processor import process_document
from app.core.vector_store import get_dense_collection
from app.services.ingestion import IngestionService
from app.models.database import SessionLocal
from app.models.document import Document, Chunk
from app.config import settings


def offline_ingest(data_dir: str = None):
    if data_dir is None:
        data_dir = settings.UPLOAD_DIR

    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return

    files = glob.glob(os.path.join(data_dir, "*.*"))
    if not files:
        print(f"数据目录下没有文件: {data_dir}")
        return

    db = SessionLocal()
    service = IngestionService()

    total_chunks = 0
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in ("pdf", "csv", "xlsx", "xls", "txt"):
            continue

        filename = os.path.basename(file_path)
        print(f"正在处理: {filename}")

        existing = db.query(Document).filter(Document.filename == filename).first()
        if existing:
            print(f"  跳过(已存在): {filename}")
            continue

        doc = Document(
            filename=filename,
            file_path=file_path,
            file_type=ext,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            chunks = process_document(file_path, ext)
            count = service.ingest_chunks(chunks, doc.id, db)
            doc.chunk_count = count
            doc.status = "completed"
            db.commit()
            total_chunks += count
            print(f"  完成, 切片数: {count}")
        except Exception as e:
            doc.status = "failed"
            db.commit()
            print(f"  处理失败: {e}")

    db.close()
    print(f"\n离线导入完成! 总切片数: {total_chunks}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default=None)
    args = parser.parse_args()
    offline_ingest(args.data_dir)
