"""Minimal vector + keyword retrievers."""
from typing import List, Dict, Any

import numpy as np
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from retrieval.indexing import tokenize


class VectorRetriever:
    """FAISS vector retriever."""

    def __init__(self, faiss_store: FAISS):
        self.faiss_store = faiss_store

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve top_k chunks using FAISS."""
        results = self.faiss_store.similarity_search_with_score(query, k=top_k)

        retrieved: List[Dict[str, Any]] = []
        for doc, dist in results:
            similarity_score = 1.0 / (1.0 + float(dist))
            md = doc.metadata or {}
            
            retrieved.append({
                "source": md.get("source", ""),
                "chunk_id": md.get("chunk_id", ""),
                "text": doc.page_content,
                "score_vector": float(similarity_score),
                "score_keyword": 0.0,
                "chunk_index": md.get("chunk_index", -1),
            })

        return retrieved


class KeywordRetriever:
    """BM25 keyword retriever."""

    def __init__(self, bm25_index: BM25Okapi, chunks: List[Dict[str, Any]]):
        self.bm25_index = bm25_index
        self.chunks = chunks

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve top_k chunks using BM25."""
        query_tokens = tokenize(query)
        scores = self.bm25_index.get_scores(query_tokens)

        top_indices = np.argsort(scores)[::-1][:top_k]
        
        max_score = float(scores[top_indices[0]]) if len(top_indices) > 0 and float(scores[top_indices[0]]) > 0 else 1.0
        if max_score == 0:
            max_score = 1.0

        retrieved: List[Dict[str, Any]] = []
        for idx in top_indices:
            if float(scores[idx]) <= 0:
                continue

            chunk = self.chunks[int(idx)]
            norm = float(scores[idx] / max_score)

            retrieved.append({
                "source": chunk.get("source", ""),
                "chunk_id": chunk.get("chunk_id", ""),
                "text": chunk.get("text", ""),
                "score_vector": 0.0,
                "score_keyword": norm,
                "chunk_index": chunk.get("chunk_index", -1),
            })

        return retrieved


def combine_results(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    top_k: int,
    alpha: float,
) -> List[Dict[str, Any]]:
    """
    Minimal hybrid combiner: dedupe by chunk_id + weighted score.
    
    alpha: weight for vector score (1-alpha for keyword)
    """
    chunk_dict: Dict[str, Dict[str, Any]] = {}

    for r in vector_results:
        cid = r.get("chunk_id", "")
        if cid:
            chunk_dict[cid] = r.copy()

    for r in keyword_results:
        cid = r.get("chunk_id", "")
        if not cid:
            continue
        
        if cid in chunk_dict:
            chunk_dict[cid]["score_keyword"] = r.get("score_keyword", 0.0)
            if r.get("text", "").strip():
                chunk_dict[cid]["text"] = r["text"]
        else:
            chunk_dict[cid] = r.copy()

    combined: List[Dict[str, Any]] = []
    for cid, data in chunk_dict.items():
        sv = float(data.get("score_vector", 0.0))
        sk = float(data.get("score_keyword", 0.0))
        score = alpha * sv + (1.0 - alpha) * sk

        out = data.copy()
        out["score"] = float(score)
        combined.append(out)

    combined.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return combined[:top_k]
