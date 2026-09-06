import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.database import engine, Base
from app.models.product import Product
from app.models.document import Document, Chunk


def init_db():
    print("正在创建数据库表结构...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")


if __name__ == "__main__":
    init_db()
