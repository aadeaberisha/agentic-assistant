"""Document indexing orchestrator (minimal hybrid)."""
import time
from typing import List, Dict, Tuple, Any

from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from retrieval.loaders import load_documents
from retrieval.chunking import chunk_documents, documents_to_dicts
from retrieval.indexing import build_faiss_index, build_bm25_index, save_indexes, load_indexes


__all__ = ["load_or_build_indexes"]


def load_or_build_indexes(
    force_rebuild: bool = False,
) -> Tuple[FAISS, BM25Okapi, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load or build FAISS + BM25 indexes from same chunk list.
    
    Returns:
        (faiss_store, bm25_index, chunks, metrics)
    """
    metrics: Dict[str, Any] = {}

    if not force_rebuild:
        loaded = load_indexes()
        if loaded is not None:
            faiss_store, bm25_index, chunks = loaded
            
            unique_sources = len(set(c.get("source", "") for c in chunks))
            
            metrics.update({
                "index_build_ms": 0,
                "index_loaded": True,
                "doc_count_unique_sources": unique_sources,
                "chunk_count": len(chunks),
            })
            
            return faiss_store, bm25_index, chunks, metrics

    start_time = time.time()

    docs = load_documents(DATA_DIR)
    if not docs:
        raise ValueError(f"No documents found in {DATA_DIR}")

    doc_chunks = chunk_documents(docs, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = documents_to_dicts(doc_chunks)

    if not chunks:
        raise ValueError("No chunks generated after chunking")

    final_chunks = [c for c in chunks if c.get("text", "").strip()]
    
    if not final_chunks:
        raise ValueError("No valid chunks with non-empty text")

    faiss_store = build_faiss_index(final_chunks)
    bm25_index = build_bm25_index(final_chunks)
    
    save_indexes(faiss_store, final_chunks)

    unique_sources = len(set(c.get("source", "") for c in final_chunks))
    
    metrics.update({
        "index_build_ms": int((time.time() - start_time) * 1000),
        "index_loaded": False,
        "doc_count_unique_sources": unique_sources,
        "chunk_count": len(final_chunks),
    })

    return faiss_store, bm25_index, final_chunks, metrics
