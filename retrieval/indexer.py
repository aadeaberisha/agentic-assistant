"""
Document ingestion + indexing orchestrator.
Main entry: load_or_build_indexes()
"""
import time
from typing import List, Dict, Tuple, Any

from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from retrieval.loaders import load_documents
from retrieval.chunking import chunk_documents
from retrieval.indexing import (
    EMBEDDING_MODEL,
    build_faiss_index,
    build_bm25_index,
    save_indexes,
    load_indexes,
)


__all__ = ["load_or_build_indexes"]


def load_or_build_indexes(
    force_rebuild: bool = False,
) -> Tuple[FAISS, BM25Okapi, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load or build FAISS + BM25 indexes.
    Returns ready-to-use retrieval indexes plus lightweight build/load metrics.
    """
    metrics: Dict[str, Any] = {}

    if not force_rebuild:
        loaded = load_indexes()
        if loaded is not None:
            faiss_store, bm25_index, chunks = loaded
            metrics.update({
                "index_build_ms": 0,
                "index_loaded": True,
                "doc_count": len(set(c.get("source", "") for c in chunks)),
                "chunk_count": len(chunks),
            })
            return faiss_store, bm25_index, chunks, metrics

    start_time = time.time()

    docs = load_documents(DATA_DIR)
    if not docs:
        raise ValueError(f"No documents found in {DATA_DIR}")

    chunks = chunk_documents(
        docs,
        model=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    faiss_store = build_faiss_index(chunks)
    bm25_index = build_bm25_index(chunks)

    save_indexes(faiss_store, chunks)

    doc_count = len(docs)
    chunk_count = len(chunks)
    
    metrics.update(
        {
            "index_build_ms": int((time.time() - start_time) * 1000),
            "index_loaded": False,
            "doc_count": doc_count,
            "chunk_count": chunk_count,
        }
    )

    return faiss_store, bm25_index, chunks, metrics