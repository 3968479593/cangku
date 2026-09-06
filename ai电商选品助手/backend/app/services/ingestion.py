import uuid

from sqlalchemy.orm import Session

from app.core.embedding import encode_dense
from app.core.vector_store import add_to_chroma
from app.models.document import Chunk


class IngestionService:

    def ingest_chunks(self, chunks: list[dict], document_id: int, db: Session) -> int:
        dense_texts = [c["content"] for c in chunks]

        dense_embs = encode_dense(dense_texts)

        dense_ids = []
        chunk_records = []

        for i, chunk in enumerate(chunks):
            dense_id = f"dense_{uuid.uuid4().hex}"
            dense_ids.append(dense_id)

            chunk_records.append(Chunk(
                document_id=document_id,
                chunk_index=chunk["index"],
                content=chunk["content"],
                token_count=len(chunk["content"]),
                chroma_dense_id=dense_id,
            ))

        add_to_chroma(
            dense_ids,
            dense_embs,
            [{"source": c["source"], "chunk_index": c["index"]} for c in chunks],
            [c["content"] for c in chunks],
        )

        db.add_all(chunk_records)
        db.commit()

        return len(chunks)
