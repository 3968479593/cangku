from app.config import settings


def reciprocal_rank_fusion(
    dense_ids: list[str],
    dense_distances: list[float],
    sparse_ids: list[str],
    sparse_distances: list[float],
    k: int = None,
) -> list[tuple[str, float]]:
    if k is None:
        k = settings.RRF_K

    scores: dict[str, float] = {}

    for rank, chunk_id in enumerate(dense_ids):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)

    for rank, chunk_id in enumerate(sparse_ids):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items
