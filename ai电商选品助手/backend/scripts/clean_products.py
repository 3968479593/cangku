# -*- coding: utf-8 -*-
"""清理指定 CSV 导入的商品：删 products 表 + Chroma 向量 + Document 记录。
用法：py -3.11 scripts/clean_products.py [文件名关键字]
默认清理 products_2026_hot.csv（不含 _2）。
"""
import sys
import os

# 把 backend 根加入 sys.path，使 import app 可用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.models.database import SessionLocal
from app.models.product import Product
from app.models.document import Document
from app.core.vector_store import delete_from_chroma

# 关键字：精确匹配 products_2026_hot.csv（结尾带 .csv，排除 _2.csv）
keyword = sys.argv[1] if len(sys.argv) > 1 else 'products_2026_hot.csv'

db = SessionLocal()
try:
    # 1. 查匹配的商品
    products = db.query(Product).filter(Product.source_doc.like(f'%{keyword}')).all()
    print(f'匹配 source_doc LIKE %*{keyword}*：{len(products)} 件商品')
    for p in products[:10]:
        print(f'  - {p.name} | source_doc={p.source_doc}')
    if len(products) > 10:
        print(f'  ... 共 {len(products)} 件（仅显示前 10）')

    # 2. 删 Chroma 向量
    chroma_ids = [p.chroma_dense_id for p in products if p.chroma_dense_id]
    if chroma_ids:
        try:
            delete_from_chroma(chroma_ids)
            print(f'已从 Chroma 删除 {len(chroma_ids)} 个向量')
        except Exception as e:
            print(f'Chroma 删除失败（不影响 MySQL 清理）：{e}')

    # 3. 删 products 表记录
    for p in products:
        db.delete(p)
    db.commit()
    print(f'已从 products 表删除 {len(products)} 件商品')

    # 4. 删 Document 表对应记录（filename = 原文件名）
    docs = db.query(Document).filter(Document.filename.like(f'%{keyword}%')).all()
    print(f'匹配 Document.filename LIKE %*{keyword}*%：{len(docs)} 条记录')
    for d in docs:
        # 顺便删物理文件
        try:
            if d.file_path and os.path.exists(d.file_path):
                os.remove(d.file_path)
        except Exception as e:
            print(f'  物理文件删除失败 {d.file_path}: {e}')
        db.delete(d)
    db.commit()
    print(f'已从 documents 表删除 {len(docs)} 条记录')

    # 5. 汇总当前剩余
    total = db.query(Product).count()
    print(f'\n清理完成。当前 products 表剩余 {total} 件商品。')
finally:
    db.close()
