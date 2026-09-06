import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

_client = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_dense_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_DENSE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def add_to_chroma(ids: list[str], embeddings: list, metadatas: list[dict], documents: list[str]):
    col = get_dense_collection()
    col.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents,
    )


def query_chroma(query_embedding, top_k: int = 20) -> dict:
    col = get_dense_collection()
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def delete_from_chroma(ids: list[str]):
    """从稠密向量集合删除指定 id 的向量。"""
    if not ids:
        return
    col = get_dense_collection()
    col.delete(ids=ids)
