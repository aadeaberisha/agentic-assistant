"""FAISS and BM25 indexing (minimal)."""
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
    """Tokenize text for BM25 (single source of truth)."""
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def build_faiss_index(chunks: List[Dict[str, Any]]) -> FAISS:
    """Build FAISS vector index with defensive empty-text filtering."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    embeddings = OpenAIEmbeddings(openai_api_key=api_key, model=EMBEDDING_MODEL)
    
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    
    for c in chunks:
        text = c.get("text", "")
        if not text or not text.strip():
            continue
        
        texts.append(text)
        metadatas.append({
            "chunk_id": c.get("chunk_id", ""),
            "source": c.get("source", ""),
            "chunk_index": c.get("chunk_index", -1),
        })
    
    if not texts:
        raise ValueError("No valid chunks with non-empty text to index")

    return FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)


def build_bm25_index(chunks: List[Dict[str, Any]]) -> BM25Okapi:
    """Build BM25 index from chunks."""
    tokenized_texts: List[List[str]] = [tokenize(c.get("text", "")) for c in chunks]
    return BM25Okapi(tokenized_texts)


def save_indexes(faiss_store: FAISS, chunks: List[Dict[str, Any]]) -> None:
    """Save FAISS index and chunks metadata."""
    index_path = Path(INDEX_DIR)
    index_path.mkdir(parents=True, exist_ok=True)

    faiss_path = index_path / "faiss_index"
    faiss_store.save_local(str(faiss_path))

    with open(index_path / "chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)


def load_indexes() -> Optional[Tuple[FAISS, BM25Okapi, List[Dict[str, Any]]]]:
    """Load FAISS index and chunks, rebuild BM25."""
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
