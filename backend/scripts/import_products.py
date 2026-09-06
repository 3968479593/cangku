"""
商品数据导入脚本

将 CSV/Excel 商品文件导入到 MySQL(products表) + ChromaDB(向量库)

CSV 列要求（表头）:
    name, category, price, platform, sales_volume, rating, description

用法:
    python scripts/import_products.py --file data/products.csv
"""

import argparse
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from app.core.embedding import encode_dense
from app.core.vector_store import add_to_chroma
from app.models.database import SessionLocal
from app.models.product import Product


REQUIRED_COLUMNS = ["name", "category", "price", "platform", "sales_volume", "rating", "description"]


def import_products(file_path: str):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        print(f"不支持的文件类型: {ext}")
        return

    # Validate columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        print(f"缺少必要列: {missing}")
        print(f"当前列: {list(df.columns)}")
        print(f"需要: {REQUIRED_COLUMNS}")
        return

    db = SessionLocal()
    total = 0

    for _, row in df.iterrows():
        # Build a rich text representation for embedding
        embed_text = (
            f"商品名称: {row['name']}; "
            f"品类: {row['category']}; "
            f"价格: {row['price']}元; "
            f"平台: {row['platform']}; "
            f"月销量: {row['sales_volume']}件; "
            f"评分: {row['rating']}分; "
            f"描述: {row['description']}"
        )

        # Embed and store in ChromaDB
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

        # Store metadata in MySQL
        product = Product(
            name=str(row["name"]),
            category=str(row["category"]) if pd.notna(row["category"]) else None,
            price=float(row["price"]) if pd.notna(row["price"]) else None,
            platform=str(row["platform"]) if pd.notna(row["platform"]) else None,
            sales_volume=int(row["sales_volume"]) if pd.notna(row["sales_volume"]) else 0,
            rating=float(row["rating"]) if pd.notna(row["rating"]) else 0,
            description=str(row["description"]) if pd.notna(row["description"]) else None,
            source_doc=os.path.basename(file_path),
            chroma_dense_id=chroma_id,
        )
        db.add(product)
        total += 1

        if total % 10 == 0:
            db.commit()
            print(f"  已导入 {total} 条...")

    db.commit()
    db.close()
    print(f"\n导入完成！共 {total} 条商品数据")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入商品数据到检索库")
    parser.add_argument("--file", type=str, required=True, help="商品 CSV/Excel 文件路径")
    args = parser.parse_args()
    import_products(args.file)
