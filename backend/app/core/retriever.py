from app.core.embedding import encode_dense
from app.core.vector_store import query_chroma
from app.config import settings


def retrieve(query: str, top_k: int = None) -> dict:
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    dense_emb = encode_dense([query])[0]
    return query_chroma(dense_emb, top_k=top_k)
