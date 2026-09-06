from typing import Optional

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.retrieval import RetrievalService


class RecommendationService:

    def __init__(self, db: Session):
        self.db = db
        self.retrieval = RetrievalService()

    def recommend_by_query(self, query: str, top_k: int = 5) -> list[dict]:
        results = self.retrieval.search(query, top_k=top_k)
        recommended = []
        for chunk_id, text, score in results:
            product = self.db.query(Product).filter(
                Product.chroma_dense_id == chunk_id
            ).first()
            if product:
                recommended.append({
                    "product": product,
                    "score": score,
                    "matched_text": text,
                })
        return recommended

    def recommend_by_category(self, category: str, limit: int = 10) -> list[Product]:
        return (
            self.db.query(Product)
            .filter(Product.category == category)
            .order_by(Product.sales_volume.desc())
            .limit(limit)
            .all()
        )
