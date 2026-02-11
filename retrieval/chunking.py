"""
Simple token-based chunking using tiktoken.
"""
from typing import Any, Dict, List

import tiktoken

from config import CHUNK_OVERLAP, CHUNK_SIZE


def get_encoder(model: str) -> tiktoken.Encoding:
    """Return the tiktoken encoder for a model; fall back to cl100k_base."""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def chunk_text_tokens(
    *,
    text: str,
    source: str,
    model: str,
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping token windows using tiktoken.
    
    Returns chunks with: source, chunk_id, text, token_count, start_char=-1, end_char=-1
    """
    if overlap >= chunk_size:
        raise ValueError(f"CHUNK_OVERLAP ({overlap}) must be < CHUNK_SIZE ({chunk_size})")

    raw = text or ""
    if not raw.strip():
        return []

    enc = get_encoder(model)
    token_ids = enc.encode(raw)

    if len(token_ids) <= chunk_size:
        return [
            {
                "source": source,
                "chunk_id": f"{source}::chunk_0",
                "text": raw.strip(),
                "start_char": -1,
                "end_char": -1,
                "token_count": len(token_ids),
            }
        ]

    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0
    start_tok = 0

    while start_tok < len(token_ids):
        end_tok = min(start_tok + chunk_size, len(token_ids))
        window_ids = token_ids[start_tok:end_tok]
        decoded = enc.decode(window_ids).strip()

        if not decoded:
            start_tok += 1
            continue

        chunks.append(
            {
                "source": source,
                "chunk_id": f"{source}::chunk_{chunk_idx}",
                "text": decoded,
                "start_char": -1,
                "end_char": -1,
                "token_count": len(window_ids),
            }
        )

        chunk_idx += 1
        next_start = end_tok - overlap
        if next_start <= start_tok:
            next_start = start_tok + 1
        start_tok = next_start

    return chunks


def chunk_documents(
    docs: List[Dict[str, str]],
    *,
    model: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Chunk a list of documents into chunk dictionaries using token-based chunking.
    """
    chunks: List[Dict[str, Any]] = []

    for doc in docs:
        source = doc.get("source", "unknown")
        text = (doc.get("text") or "").strip()
        if not text:
            continue

        chunks.extend(
            chunk_text_tokens(
                text=text,
                source=source,
                model=model,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
            )
        )

    return chunks
