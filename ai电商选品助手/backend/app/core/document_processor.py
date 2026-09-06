import os
import uuid
from typing import Optional

import pandas as pd
from PyPDF2 import PdfReader

from app.config import settings


def parse_document(file_path: str, file_type: str) -> list[str]:
    texts = []
    if file_type == "csv":
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            texts.append(row.to_string())
    elif file_type in ("xlsx", "xls"):
        df = pd.read_excel(file_path)
        for _, row in df.iterrows():
            texts.append(row.to_string())
    elif file_type == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                texts.append(text.strip())
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            texts.append(content)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    return texts


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 100,
    separators: Optional[list[str]] = None,
) -> list[str]:
    if separators is None:
        separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", " "]

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if end < len(text):
            best_split = -1
            for sep in separators:
                pos = chunk.rfind(sep)
                if pos > best_split:
                    best_split = pos
            if best_split > chunk_size // 2:
                end = start + best_split + 1
                chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        # Reached the end — stop to avoid infinite loop
        if end >= len(text):
            break

        start = end - chunk_overlap

    return chunks


def process_document(file_path: str, file_type: str) -> list[dict]:
    texts = parse_document(file_path, file_type)

    all_chunks = []
    for text in texts:
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "content": chunk,
                "index": i,
                "source": os.path.basename(file_path),
            })

    return all_chunks
