"""
Retrievers (Vector + Keyword) + Hybrid combiner.
Low-level retrieval primitives.
No agent or orchestration logic should live here.
"""
from typing import List, Dict, Any

import numpy as np
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from retrieval.indexing import tokenize


class KeywordRetriever:
    """BM25 keyword retriever."""

    def __init__(self, bm25_index: BM25Okapi, chunks: List[Dict[str, Any]]):
        self.bm25_index = bm25_index
        self.chunks = chunks

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        query_tokens = tokenize(query)
        scores = self.bm25_index.get_scores(query_tokens)

        top_indices = np.argsort(scores)[::-1][:top_k]

        max_score = (
            float(scores[top_indices[0]])
            if len(top_indices) > 0 and float(scores[top_indices[0]]) > 0
            else 1.0
        )
        if max_score == 0:
            max_score = 1.0

        retrieved: List[Dict[str, Any]] = []
        for idx in top_indices:
            if float(scores[idx]) <= 0:
                continue

            chunk = self.chunks[int(idx)]
            norm = float(scores[idx] / max_score)

            retrieved.append(
                {
                    "source": chunk.get("source", ""),
                    "chunk_id": chunk.get("chunk_id", ""),
                    "text": chunk.get("text", ""),
                    "score_vector": 0.0,
                    "score_keyword": norm,
                }
            )

        return retrieved


class VectorRetriever:
    """FAISS vector retriever."""

    def __init__(self, faiss_store: FAISS):
        self.faiss_store = faiss_store

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        results = self.faiss_store.similarity_search_with_score(query, k=top_k)

        retrieved: List[Dict[str, Any]] = []
        for doc, dist in results:
            # Treat dist as L2 distance (>= 0). Convert to bounded similarity in [0, 1].
            similarity_score = 1.0 / (1.0 + float(dist))

            md = doc.metadata or {}
            retrieved.append(
                {
                    "source": md.get("source", ""),
                    "chunk_id": md.get("chunk_id", ""),
                    "text": doc.page_content,
                    "score_vector": float(similarity_score),
                    "score_keyword": 0.0,
                }
            )

        return retrieved


def combine_results(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    top_k: int,
    alpha: float,
) -> List[Dict[str, Any]]:
    """
    Combine vector + keyword results with weighted scoring.
    Adds "score" field and returns top_k by combined score.
    """
    chunk_dict: Dict[str, Dict[str, Any]] = {}

    for r in vector_results:
        cid = r.get("chunk_id", "")
        if not cid:
            continue
        chunk_dict[cid] = r.copy()

    for r in keyword_results:
        cid = r.get("chunk_id", "")
        if not cid:
            continue
        if cid in chunk_dict:
            chunk_dict[cid]["score_keyword"] = r.get("score_keyword", 0.0)
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