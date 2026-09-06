import json
import logging
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.product import Product
from app.models.schemas import ChatRequest, ChatResponse, SearchResult, ProductOut
from app.services.retrieval import RetrievalService
from app.services.statistics import compute_category_stats
from app.core.llm import chat_with_history, chat_with_history_stream

logger = logging.getLogger(__name__)
router = APIRouter()

conversations: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 20

ANALYSIS_KEYWORDS = [
    "选品", "品类", "销量", "爆款", "趋势", "分析", "排名", "推荐",
    "哪个好", "什么好", "最好", "热销", "蓝海", "商品", "产品",
    "家居", "女装", "美妆", "数码", "食品", "母婴", "宠物", "运动",
    "厨房", "浴室", "收纳", "防晒", "大码", "卖什么", "好卖",
    "前景", "赚钱", "值得", "能做", "好做",
]

FOLLOW_UP_WORDS = ["类似", "同款", "这种", "一样的", "还有", "别的", "再推荐"]


DEEP_ANALYSIS_WORDS = ["前景", "值得", "能不能", "能做吗", "好做吗", "赚钱吗"]


def _is_deep_analysis(query: str) -> bool:
    """前景类问题 → 五段深度分析"""
    return any(w in query for w in DEEP_ANALYSIS_WORDS)


def _is_analysis_query(query: str, history: list[dict] = None) -> bool:
    if any(kw in query for kw in ANALYSIS_KEYWORDS):
        return True
    if any(kw in query for kw in FOLLOW_UP_WORDS):
        return True
    if history and len(history) >= 2:
        last_assistant = history[-1].get("content", "")
        if any(w in last_assistant for w in ["均价", "平均销量", "利好因素", "核心风险"]):
            return True
    return False


def _build_query_with_context(query: str, history: list[dict]) -> str:
    if not history:
        return query
    last_user_msg = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break
    if not last_user_msg:
        return query
    if any(w in query for w in FOLLOW_UP_WORDS):
        return f'上文用户问的是：「{last_user_msg}」。现在用户追问：{query}（请在同一个品类范围内推荐类似商品，不要跨品类）'
    return query


def _format_output(text: str) -> str:
    """强制格式化：板块标题前空行、每个条目独立一行。"""
    # 板块标题（一、到 五、）前加两个换行
    for i in range(5):
        cn = ['一', '二', '三', '四', '五'][i]
        text = text.replace(f'{cn}、', f'\n\n{cn}、')
    # 每个「 - 」前加换行
    text = text.replace(' - ', '\n- ')
    # 合并多余空行
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text.strip()


def _resolve_request(query: str, history: list[dict], db: Session):
    """分析/普通两种模式的公共前置处理，返回 (enriched_query, context_texts, retrieval_results)。"""
    if _is_analysis_query(query, history):
        enriched_query = _build_query_with_context(query, history)
        mode = 'A' if _is_deep_analysis(query) else 'B'
        enriched_query = f'[使用方式{mode}回答] {enriched_query}'
        stats_text = compute_category_stats(db, query=enriched_query)
        service = RetrievalService()
        retrieval_results = service.search(enriched_query)
        context_texts = [stats_text] + [text for _, text, _ in retrieval_results]
    else:
        enriched_query = query
        retrieval_results = []
        context_texts = []
    return enriched_query, context_texts, retrieval_results


def _build_sources(retrieval_results: list, db: Session) -> list[SearchResult]:
    """把检索结果映射为带商品详情的来源列表。"""
    sources = []
    for chunk_id, text, score in retrieval_results:
        product = db.query(Product).filter(
            Product.chroma_dense_id == chunk_id
        ).first()
        if product:
            sources.append(SearchResult(
                product=ProductOut.model_validate(product),
                score=score,
                matched_chunk=text,
            ))
    return sources


def _append_history(cid: str, history: list[dict], query: str, answer: str):
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]
    conversations[cid] = history


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    try:
        cid = req.conversation_id or str(uuid.uuid4())
        history = conversations.get(cid, [])

        enriched_query, context_texts, retrieval_results = _resolve_request(req.query, history, db)
        raw = chat_with_history(enriched_query, context_texts, history, deep_thinking=req.deep_thinking)
        answer = _format_output(raw) if retrieval_results else raw

        _append_history(cid, history, req.query, answer)
        sources = _build_sources(retrieval_results, db)

        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=cid,
        )
    except Exception as e:
        logger.exception("对话处理失败: %s", e)
        raise HTTPException(status_code=500, detail="对话服务出错，请稍后重试")


@router.post("/stream")
def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """流式对话：SSE 推送 sources / reasoning / content / done 事件。"""
    try:
        cid = req.conversation_id or str(uuid.uuid4())
        history = conversations.get(cid, [])

        enriched_query, context_texts, retrieval_results = _resolve_request(req.query, history, db)
        sources = _build_sources(retrieval_results, db)

        def event_stream():
            yield _sse({"type": "sources", "sources": [s.model_dump(mode="json") for s in sources]})

            answer_parts: list[str] = []
            try:
                for kind, text in chat_with_history_stream(
                    enriched_query, context_texts, history, deep_thinking=req.deep_thinking
                ):
                    if kind == "reasoning":
                        yield _sse({"type": "reasoning", "delta": text})
                    else:
                        answer_parts.append(text)
                        yield _sse({"type": "content", "delta": text})
            except Exception as e:
                logger.exception("LLM 流式调用失败: %s", e)
                yield _sse({"type": "error", "message": "生成失败，请稍后重试"})

            answer = "".join(answer_parts)
            if answer:
                _append_history(cid, history, req.query, answer)

            yield _sse({"type": "done", "conversation_id": cid})

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.exception("对话处理失败: %s", e)
        raise HTTPException(status_code=500, detail="对话服务出错，请稍后重试")


@router.delete("/conversation/{conversation_id}")
def clear_conversation(conversation_id: str):
    conversations.pop(conversation_id, None)
    return {"message": "对话已清空"}
