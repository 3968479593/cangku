import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text, or_
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models.product import Product
from app.models.schemas import (
    ProductOut, ProductListResponse, FiltersInfo, RecommendedProduct,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=ProductListResponse)
def list_products(
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: str = Query("sales_desc", pattern="^(sales_desc|sales_asc|price_asc|price_desc|rating_desc|newest)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    if platform:
        q = q.filter(Product.platform == platform)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    total = q.count()

    if sort_by == "sales_asc":
        q = q.order_by(Product.sales_volume.asc())
    elif sort_by == "price_asc":
        q = q.order_by(Product.price.asc().nullslast())
    elif sort_by == "price_desc":
        q = q.order_by(Product.price.desc().nullslast())
    elif sort_by == "rating_desc":
        q = q.order_by(Product.rating.desc().nullslast())
    elif sort_by == "newest":
        q = q.order_by(Product.created_at.desc())
    else:  # sales_desc
        q = q.order_by(Product.sales_volume.desc())

    skip = (page - 1) * page_size
    items = q.offset(skip).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/recommended", response_model=list[RecommendedProduct])
def recommended_products(
    limit: int = Query(8, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """推荐潜力商品：综合销量 × 评分排序。"""
    products = db.query(Product).filter(
        Product.rating > 0,
        Product.sales_volume > 0,
    ).order_by(
        (func.coalesce(Product.sales_volume, 0) * func.coalesce(Product.rating, 0)).desc()
    ).limit(limit).all()

    result = []
    for p in products:
        pot = (p.sales_volume or 0) * (p.rating or 0) / 1000
        result.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "platform": p.platform,
            "sales_volume": p.sales_volume,
            "rating": p.rating,
            "description": p.description,
            "source_doc": p.source_doc,
            "created_at": p.created_at,
            "potential_score": round(pot, 1),
        })
    return result


@router.get("/filters", response_model=FiltersInfo)
def get_filters(db: Session = Depends(get_db)):
    """获取筛选配置：类目列表、价格范围、平台列表。"""
    cats = db.query(Product.category).filter(
        Product.category != None,
    ).distinct().order_by(Product.category).all()
    categories = [c[0] for c in cats if c[0]]

    platforms = db.query(Product.platform).filter(
        Product.platform != None,
    ).distinct().order_by(Product.platform).all()
    platforms = [p[0] for p in platforms if p[0]]

    price_min = db.query(func.min(Product.price)).filter(Product.price != None).scalar() or 0
    price_max = db.query(func.max(Product.price)).filter(Product.price != None).scalar() or 10000

    return {
        "categories": categories,
        "price_min": round(float(price_min), 2),
        "price_max": round(float(price_max), 2),
        "platforms": platforms,
    }


@router.get("/stats")
def product_stats(db: Session = Depends(get_db)):
    """商品数据看板：指标汇总 + 三类图表数据。"""
    # 1. 基础指标
    total = db.query(func.count(Product.id)).scalar() or 0
    hot_count = db.query(func.count(Product.id)).filter(Product.sales_volume >= 50000).scalar() or 0
    # 库存预警：销量极低的商品（销量 < 10000 视为滞销/库存预警）
    alert_count = db.query(func.count(Product.id)).filter(
        (Product.sales_volume < 10000) | (Product.sales_volume == None)
    ).scalar() or 0

    # 2. 类目分布（饼图）
    category_rows = db.query(
        Product.category,
        func.count(Product.id).label('cnt'),
    ).filter(Product.category != None
    ).group_by(Product.category
    ).order_by(func.count(Product.id).desc()
    ).limit(10).all()

    category_distribution = [
        {"name": r[0], "value": int(r[1])}
        for r in category_rows
    ]

    # 如果有其他类目被 limit 截断，合并为"其他"
    if total and len(category_distribution) >= 10:
        other_count = total - sum(c["value"] for c in category_distribution)
        if other_count > 0:
            category_distribution.append({"name": "其他", "value": other_count})

    # 3. 价格区间分布（柱状图）
    price_buckets = [
        ("0-50",   0,    50),
        ("50-100", 50,   100),
        ("100-500", 100, 500),
        ("500-1000", 500, 1000),
        ("1000-5000", 1000, 5000),
        ("5000+",   5000, None),
    ]
    price_distribution = []
    for name, low, high in price_buckets:
        q = db.query(func.count(Product.id)).filter(Product.price != None)
        if high is None:
            q = q.filter(Product.price >= low)
        else:
            q = q.filter(Product.price >= low, Product.price < high)
        cnt = q.scalar() or 0
        price_distribution.append({"name": name, "value": int(cnt)})

    # 4. 平台销量对比（横向条形图：各平台商品总销量 + 商品数）
    platform_rows = db.query(
        Product.platform,
        func.count(Product.id).label('cnt'),
        func.sum(func.coalesce(Product.sales_volume, 0)).label('total_sales'),
    ).filter(Product.platform != None
    ).group_by(Product.platform
    ).order_by(func.sum(func.coalesce(Product.sales_volume, 0)).desc()
    ).all()

    platform_sales = [
        {"name": r[0], "sales": int(r[2] or 0), "count": int(r[1])}
        for r in platform_rows
    ]

    return {
        "summary": {
            "total_products": int(total),
            "hot_products": int(hot_count),
            "stock_alerts": int(alert_count),
            "category_count": len(category_distribution),
        },
        "category_distribution": category_distribution,
        "price_distribution": price_distribution,
        "platform_sales": platform_sales,
    }


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "商品不存在")
    return product
