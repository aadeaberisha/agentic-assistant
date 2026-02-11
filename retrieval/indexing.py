"""
Index building + persistence (FAISS + BM25).
SINGLE source of truth for:
- EMBEDDING_MODEL
- tokenize()
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from config import INDEX_DIR

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def tokenize(text: str) -> List[str]:
    """
    Regex tokenization for BM25 (must match in both indexing and querying).
    """
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def build_faiss_index(chunks: List[Dict[str, Any]]) -> FAISS:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    embeddings = OpenAIEmbeddings(openai_api_key=api_key, model=EMBEDDING_MODEL)

    texts = [c["text"] for c in chunks]
    metadatas = [{"chunk_id": c["chunk_id"], "source": c["source"]} for c in chunks]

    return FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)


def build_bm25_index(chunks: List[Dict[str, Any]]) -> BM25Okapi:
    """
    Build BM25 index from chunks. BM25 stores tokenized data internally.
    Note: BM25 index is rebuilt from chunks on load to keep persistence simple.
    """
    tokenized_texts: List[List[str]] = [tokenize(c.get("text", "")) for c in chunks]
    return BM25Okapi(tokenized_texts)


def save_indexes(
    faiss_store: FAISS,
    chunks: List[Dict[str, Any]],
) -> None:
    """
    Save FAISS index and chunks metadata.
    BM25 is rebuilt from chunks on load (no separate persistence needed).
    """
    index_path = Path(INDEX_DIR)
    index_path.mkdir(parents=True, exist_ok=True)

    faiss_path = index_path / "faiss_index"
    faiss_store.save_local(str(faiss_path))

    with open(index_path / "chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)


def load_indexes() -> Optional[Tuple[FAISS, BM25Okapi, List[Dict[str, Any]]]]:
    """
    Load FAISS index and chunks, rebuild BM25 from chunks.
    Returns (faiss_store, bm25_index, chunks) or None if not found.
    """
    index_path = Path(INDEX_DIR)
    faiss_path = index_path / "faiss_index"
    chunks_path = index_path / "chunks_metadata.json"

    if not (faiss_path.exists() and chunks_path.exists()):
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    embeddings = OpenAIEmbeddings(openai_api_key=api_key, model=EMBEDDING_MODEL)

    faiss_store = FAISS.load_local(
        str(faiss_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)

    bm25_index = build_bm25_index(chunks)

    return faiss_store, bm25_index, chunks