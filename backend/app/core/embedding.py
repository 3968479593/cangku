from FlagEmbedding import BGEM3FlagModel

from app.config import settings

_model = None


def get_embedding_model() -> BGEM3FlagModel:
    global _model
    if _model is None:
        _model = BGEM3FlagModel(
            settings.EMBEDDING_MODEL,
            use_fp16=settings.EMBEDDING_DEVICE != "cpu",
            device=settings.EMBEDDING_DEVICE,
            cache_dir=settings.MODEL_CACHE_DIR,
        )
    return _model


def encode_dense(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    output = model.encode(texts, return_dense=True, return_sparse=False)
    return output["dense_vecs"].tolist()


def encode_sparse(texts: list[str]) -> list[dict[int, float]]:
    model = get_embedding_model()
    output = model.encode(texts, return_dense=False, return_sparse=True)
    results = []
    for weights in output["lexical_weights"]:
        results.append({int(k): float(v) for k, v in weights.items()})
    return results
