import logging

from app.core.retriever import retrieve
from app.core.reranker import rerank
from app.config import settings

logger = logging.getLogger(__name__)


class RetrievalService:

    def search(self, query: str, top_k: int = None) -> list[tuple[str, str, float]]:
        if top_k is None:
            top_k = settings.RERANK_TOP_K

        results = retrieve(query, settings.RETRIEVAL_TOP_K)

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Convert cosine distance to similarity score (1 - distance)
        candidates = [(cid, doc, 1.0 - dist) for cid, doc, dist in zip(ids, docs, distances)]

        try:
            return rerank(query, candidates, top_k=top_k)
        except Exception as e:
            logger.warning("重排序失败，使用检索分数: %s", e)
            candidates.sort(key=lambda x: x[2], reverse=True)
            return candidates[:top_k]
