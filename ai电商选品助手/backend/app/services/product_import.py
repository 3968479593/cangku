"""商品数据导入服务：把 CSV/Excel 文件解析后写入 products 表 + Chroma。

既可被命令行脚本调用，也可被管理后台上传接口直接调用。
"""
import os
import uuid

import pandas as pd

from app.core.embedding import encode_dense
from app.core.vector_store import add_to_chroma
from app.models.product import Product

REQUIRED_COLUMNS = ["name", "category", "price", "platform", "sales_volume", "rating", "description"]


def is_product_file(file_path: str) -> bool:
    """检测文件是否为商品数据文件（CSV/Excel 且包含必要列）。"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        return False
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path, nrows=1)
        else:
            df = pd.read_excel(file_path, nrows=1)
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        return len(missing) == 0
    except Exception:
        return False


def import_products_from_file(file_path: str, db) -> int:
    """解析商品文件并写入 products 表 + Chroma，返回导入的商品数。"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要列: {missing}")

    total = 0
    source_doc = os.path.basename(file_path)

    for _, row in df.iterrows():
        name = str(row["name"]) if pd.notna(row["name"]) else ""
        if not name:
            continue

        # 查重：同名 + 同来源文件已存在则跳过
        existing = db.query(Product).filter(
            Product.name == name,
            Product.source_doc == source_doc,
        ).first()
        if existing:
            continue

        # 构建嵌入文本
        embed_text = (
            f"商品名称: {row['name']}; "
            f"品类: {row['category']}; "
            f"价格: {row['price']}元; "
            f"平台: {row['platform']}; "
            f"月销量: {row['sales_volume']}件; "
            f"评分: {row['rating']}分; "
            f"描述: {row['description']}"
        )

        # 写入 Chroma
        dense_emb = encode_dense([embed_text])[0]
        chroma_id = f"prod_{uuid.uuid4().hex}"
        add_to_chroma(
            ids=[chroma_id],
            embeddings=[dense_emb],
            metadatas=[{
                "name": str(row["name"]),
                "category": str(row["category"]),
                "platform": str(row["platform"]),
            }],
            documents=[embed_text],
        )

        # 写入 MySQL
        product = Product(
            name=name,
            category=str(row["category"]) if pd.notna(row["category"]) else None,
            price=float(row["price"]) if pd.notna(row["price"]) else None,
            platform=str(row["platform"]) if pd.notna(row["platform"]) else None,
            sales_volume=int(row["sales_volume"]) if pd.notna(row["sales_volume"]) else 0,
            rating=float(row["rating"]) if pd.notna(row["rating"]) else 0,
            description=str(row["description"]) if pd.notna(row["description"]) else None,
            source_doc=source_doc,
            chroma_dense_id=chroma_id,
        )
        db.add(product)
        total += 1

        if total % 10 == 0:
            db.commit()

    db.commit()
    return total
