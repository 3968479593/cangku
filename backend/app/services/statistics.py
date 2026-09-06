"""
品类聚合统计服务 —— 从 MySQL 计算品类级指标，注入 LLM 上下文。
支持按用户查询中的品类关键词过滤，让 LLM 聚焦用户关心的品类。
"""
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.product import Product

logger = logging.getLogger(__name__)

# 品类关键词 → 数据库品类名映射
CATEGORY_MAP: dict[str, list[str]] = {
    "家居": ["家居收纳", "厨房收纳", "浴室用品", "日用百货"],
    "收纳": ["家居收纳", "厨房收纳"],
    "女装": ["女装"],
    "防晒": ["女装"],
    "美妆": ["美妆护肤"],
    "护肤": ["美妆护肤"],
    "数码": ["数码电器"],
    "电器": ["数码电器"],
    "耳机": ["数码电器"],
    "风扇": ["数码电器"],
    "食品": ["食品饮料"],
    "零食": ["食品饮料"],
    "饮料": ["食品饮料"],
    "母婴": ["母婴"],
    "宝宝": ["母婴"],
    "儿童": ["母婴"],
    "宠物": ["宠物用品"],
    "猫": ["宠物用品"],
    "狗": ["宠物用品"],
    "运动": ["运动户外"],
    "户外": ["运动户外"],
    "健身": ["运动户外"],
    "文具": ["文具办公"],
    "办公": ["文具办公"],
    "厨房": ["厨房收纳"],
    "浴室": ["浴室用品"],
    "日用": ["日用百货"],
    "百货": ["日用百货"],
}


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0


def _resolve_categories(query: str) -> list[str] | None:
    """从用户查询中提取品类关键词，返回匹配的数据库品类名列表。"""
    matched: set[str] = set()
    for keyword, categories in CATEGORY_MAP.items():
        if keyword in query:
            matched.update(categories)
    return list(matched) if matched else None


def compute_category_stats(db: Session, query: str = "") -> str:
    """
    从 Product 表全量扫描，计算每个品类的聚合指标。
    如果 query 中包含品类关键词，自动过滤并高亮相关品类。
    返回可直接注入 LLM prompt 的格式化文本。
    """
    products = db.query(Product).all()

    if not products:
        return "（数据库暂无商品）"

    target_categories = _resolve_categories(query) if query else None

    # 按品类分组
    groups: dict[str, list] = defaultdict(list)
    for p in products:
        cat = p.category or "其他"
        groups[cat].append(p)

    lines: list[str] = []

    if target_categories:
        # ---- 聚焦模式：只展示用户关心的品类 ----
        lines.append("=" * 50)
        lines.append(f'【用户关注的品类统计数据】（查询：「{query}」）')
        lines.append("=" * 50)

        focus_groups = {cat: groups[cat] for cat in target_categories if cat in groups}
        other_groups = {cat: items for cat, items in groups.items() if cat not in target_categories}

        # 用户关注的品类详表
        lines.append(f"\n{'品类':<12} {'商品数':>6} {'均价':>8} {'平均销量':>10} {'平均评分':>8} {'最高单品销量':>12}")
        lines.append("-" * 58)
        for cat in target_categories:
            if cat not in groups:
                continue
            items = groups[cat]
            count = len(items)
            avg_price = _safe_avg([p.price for p in items if p.price])
            avg_sales = _safe_avg([p.sales_volume for p in items if p.sales_volume])
            avg_rating = _safe_avg([p.rating for p in items if p.rating])
            top = max(items, key=lambda x: x.sales_volume or 0)
            lines.append(
                f"▶ {cat:<10} {count:>6} {avg_price:>7.1f}元 {avg_sales:>9.0f}件 {avg_rating:>7.1f}分 {top.sales_volume:>10}件"
            )

        # 其他品类仅汇总一行（供对比）
        if other_groups:
            other_products = [p for items in other_groups.values() for p in items]
            other_avg_price = _safe_avg([p.price for p in other_products if p.price])
            other_avg_sales = _safe_avg([p.sales_volume for p in other_products if p.sales_volume])
            other_avg_rating = _safe_avg([p.rating for p in other_products if p.rating])
            other_total = len(other_products)
            lines.append(f"  {'其他品类':<10} {other_total:>6} {other_avg_price:>7.1f}元 {other_avg_sales:>9.0f}件 {other_avg_rating:>7.1f}分 {'-':>10}")

    else:
        # ---- 全量模式 ----
        lines.append("=" * 50)
        lines.append("【全量品类统计数据】（以下数据均为数据库真实聚合值）")
        lines.append("=" * 50)
        lines.append(f"\n{'品类':<12} {'商品数':>6} {'均价':>8} {'平均销量':>10} {'平均评分':>8} {'最高单品销量':>12}")
        lines.append("-" * 58)
        for cat, items in groups.items():
            count = len(items)
            avg_price = _safe_avg([p.price for p in items if p.price])
            avg_sales = _safe_avg([p.sales_volume for p in items if p.sales_volume])
            avg_rating = _safe_avg([p.rating for p in items if p.rating])
            top = max(items, key=lambda x: x.sales_volume or 0)
            lines.append(
                f"{cat:<12} {count:>6} {avg_price:>7.1f}元 {avg_sales:>9.0f}件 {avg_rating:>7.1f}分 {top.sales_volume:>10}件"
            )

    # ---- 以下为公共部分：Top 单品 + 预警 + 平台分布 ----
    all_sorted = sorted(products, key=lambda x: x.sales_volume or 0, reverse=True)

    # 如果有品类过滤，Top 10 也优先展示相关品类
    if target_categories:
        focus_products = [p for p in all_sorted if (p.category or "其他") in target_categories]
        other_products = [p for p in all_sorted if (p.category or "其他") not in target_categories]
        top_display = (focus_products + other_products)[:10]
    else:
        top_display = all_sorted[:10]

    lines.append(f"\n{'─' * 50}")
    lines.append("【销量 Top 10 单品】")
    lines.append(f"{'排名':<4} {'商品名':<40} {'品类':<10} {'销量':>8} {'价格':>8} {'评分':>6} {'平台':<8}")
    lines.append("-" * 90)
    for i, p in enumerate(top_display, 1):
        name = p.name[:38] + ".." if len(p.name) > 40 else p.name
        marker = "▶ " if target_categories and (p.category or "其他") in target_categories else "  "
        lines.append(
            f"{i:<4} {marker}{name:<38} {(p.category or '-'):<10} {p.sales_volume:>8} {p.price:>7.1f}元 "
            f"{p.rating:>5.1f}分 {(p.platform or '-'):<8}"
        )

    # 低评分预警
    warnings = [p for p in all_sorted if p.rating and p.rating < 4.5 and p.sales_volume and p.sales_volume > 5000]
    if warnings:
        lines.append(f"\n{'─' * 50}")
        lines.append("【低评分预警】（评分<4.5 且 销量>5000）")
        for p in warnings[:5]:
            lines.append(f"  ⚠ {p.name} | {p.rating}分 | {p.sales_volume}件 | {p.platform}")

    # 平台分布
    platform_groups = defaultdict(list)
    for p in products:
        pf = p.platform or "未知"
        platform_groups[pf].append(p.sales_volume or 0)
    lines.append(f"\n{'─' * 50}")
    lines.append("【平台分布】")
    for pf, vols in platform_groups.items():
        lines.append(f"  {pf}: {len(vols)}款商品 | 总销量{sum(vols)}件 | 均销量{_safe_avg(vols):.0f}件")

    if target_categories:
        lines.append("")
        lines.append("=" * 50)
        lines.append("【请只分析以上标注 ▶ 的用户关注品类，其他品类仅作对比参考】")
        lines.append("=" * 50)
    else:
        lines.append("")
        lines.append("=" * 50)
        lines.append("【使用以上真实统计数据回答，禁止编造任何数字】")
        lines.append("=" * 50)

    return "\n".join(lines)
