from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models.product import Product
from app.models.schemas import SearchRequest, SearchResult, ProductOut
from app.services.retrieval import RetrievalService


router = APIRouter()


@router.post("/")
def search(
    req: SearchRequest,
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: str = Query("relevance", pattern="^(relevance|sales_desc|price_asc|price_desc|rating_desc|newest)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = RetrievalService()
    # 多取一些候选，方便筛选
    top_k = max(req.top_k, 50)
    results = service.search(req.query, top_k=top_k)

    enriched = []
    for chunk_id, text, score in results:
        product = db.query(Product).filter(
            Product.chroma_dense_id == chunk_id
        ).first()

        if not product:
            continue

        # 应用筛选条件
        if category and product.category != category:
            continue
        if min_price is not None and (product.price is None or product.price < min_price):
            continue
        if max_price is not None and (product.price is None or product.price > max_price):
            continue

        enriched.append({
            "product": ProductOut.model_validate(product),
            "score": score,
            "matched_chunk": text,
        })

    # 排序
    if sort_by == "sales_desc":
        enriched.sort(key=lambda x: x["product"].sales_volume or 0, reverse=True)
    elif sort_by == "price_asc":
        enriched.sort(key=lambda x: x["product"].price or 0)
    elif sort_by == "price_desc":
        enriched.sort(key=lambda x: x["product"].price or 0, reverse=True)
    elif sort_by == "rating_desc":
        enriched.sort(key=lambda x: x["product"].rating or 0, reverse=True)
    elif sort_by == "newest":
        enriched.sort(key=lambda x: x["product"].created_at or "", reverse=True)
    # else: relevance (默认，search 结果已按 score 排序)

    total = len(enriched)
    skip = (page - 1) * page_size
    paged = enriched[skip:skip + page_size]

    return {
        "results": paged,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
