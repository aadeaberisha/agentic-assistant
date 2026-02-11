"""Hybrid retrieval facade (vector + keyword)."""
from typing import List, Dict, Any, Tuple

from retrieval.indexer import load_or_build_indexes
from retrieval.retrievers import VectorRetriever, KeywordRetriever, combine_results
from config import TOP_K, HYBRID_ALPHA


class RetrievalTool:
    """Hybrid retrieval tool (vector + keyword)."""

    def __init__(self, faiss_store, bm25_index, chunks):
        self.vector = VectorRetriever(faiss_store)
        self.keyword = KeywordRetriever(bm25_index, chunks)

    def search(
        self, 
        query: str, 
        *, 
        mode: str = "hybrid",
        top_k: int = TOP_K, 
        alpha: float = HYBRID_ALPHA
    ) -> List[Dict[str, Any]]:
        """
        Search using vector/keyword/hybrid.
        
        mode: "vector", "keyword", or "hybrid"
        """
        if mode == "vector":
            results = self.vector.retrieve(query, top_k=top_k)
            for r in results:
                r["score"] = r["score_vector"]
            return results
        
        elif mode == "keyword":
            results = self.keyword.retrieve(query, top_k=top_k)
            for r in results:
                r["score"] = r["score_keyword"]
            return results
        
        else:
            k_fetch = max(top_k * 2, top_k)
            v = self.vector.retrieve(query, top_k=k_fetch)
            k = self.keyword.retrieve(query, top_k=k_fetch)
            return combine_results(v, k, top_k=top_k, alpha=alpha)


def get_retrieval_tool(force_rebuild: bool = False) -> Tuple[RetrievalTool, Dict[str, Any]]:
    """Load or build indexes and return retrieval tool."""
    faiss_store, bm25_index, chunks, metrics = load_or_build_indexes(force_rebuild=force_rebuild)
    return RetrievalTool(faiss_store, bm25_index, chunks), metrics
