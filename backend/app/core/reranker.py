from FlagEmbedding import FlagReranker

from app.config import settings

_reranker = None


def _patch_tokenizer(reranker):
    """Add prepare_for_model compat shim for transformers v5.x.

    In transformers v5.x, prepare_for_model and encode_plus were removed.
    Build the encoding manually from pre-tokenized inputs (list[int]).
    """
    tokenizer = reranker.tokenizer
    if hasattr(tokenizer, "prepare_for_model"):
        return

    def prepare_for_model(
        ids, pair_ids=None,
        truncation="longest_first", max_length=None, padding=False,
        **kwargs
    ):
        # --- Add special tokens ---
        bos = tokenizer.bos_token_id if getattr(tokenizer, "bos_token_id", None) is not None else tokenizer.cls_token_id
        sep = tokenizer.sep_token_id if getattr(tokenizer, "sep_token_id", None) is not None else 102
        if bos is None:
            bos = 0

        if pair_ids:
            input_ids = [bos] + ids + [sep] + pair_ids + [sep]
        else:
            input_ids = [bos] + ids + [sep]

        # --- Truncation ---
        if max_length is not None and len(input_ids) > max_length:
            if truncation == "only_second" and pair_ids:
                # Keep the first sentence (with BOS), truncate second
                prefix_len = len([bos]) + len(ids) + len([sep])
                available = max_length - prefix_len
                if available > 0:
                    input_ids = [bos] + ids + [sep] + pair_ids[:available - 1] + [sep]
                else:
                    input_ids = input_ids[:max_length]
            elif truncation == "only_first":
                suffix = [sep] + pair_ids + [sep]
                available = max_length - len(suffix)
                if available > 0:
                    input_ids = [bos] + ids[:available - len([bos])] + suffix
                else:
                    input_ids = input_ids[-max_length:]
            else:
                # longest_first or default: truncate from end
                input_ids = input_ids[:max_length]

        return {
            "input_ids": input_ids,
            "token_type_ids": [0] * len(input_ids),
            "attention_mask": [1] * len(input_ids),
        }

    tokenizer.prepare_for_model = prepare_for_model


def get_reranker() -> FlagReranker:
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(
            settings.RERANKER_MODEL,
            use_fp16=settings.EMBEDDING_DEVICE != "cpu",
            cache_dir=settings.MODEL_CACHE_DIR,
        )
        _patch_tokenizer(_reranker)
    return _reranker


def rerank(
    query: str,
    candidates: list[tuple[str, str, float]],  # (chunk_id, text, initial_score)
    top_k: int = None,
) -> list[tuple[str, str, float]]:
    if top_k is None:
        top_k = settings.RERANK_TOP_K
    if not candidates:
        return []

    reranker = get_reranker()
    pairs = [[query, text] for _, text, _ in candidates]
    scores = reranker.compute_score(pairs, normalize=True)

    if isinstance(scores, float):
        scores = [scores]

    scored = [
        (cid, text, float(s))
        for (cid, text, _), s in zip(candidates, scores)
    ]
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_k]
