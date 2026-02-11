"""
High-level retrieval facade used by agents.
Abstracts away retrieval implementation details.
"""
from typing import List, Dict, Any, Tuple

from retrieval.indexer import load_or_build_indexes
from retrieval.retrievers import VectorRetriever, KeywordRetriever, combine_results
from config import TOP_K, HYBRID_ALPHA


class RetrievalTool:
    """
    Usage:
        tool, metrics = get_retrieval_tool()
        results = tool.search("query")
    """

    def __init__(self, faiss_store, bm25_index, chunks):
        self.vector = VectorRetriever(faiss_store)
        self.keyword = KeywordRetriever(bm25_index, chunks)

    def search(
        self,
        query: str,
        *,
        top_k: int = TOP_K,
        alpha: float = HYBRID_ALPHA,
    ) -> List[Dict[str, Any]]:
        v = self.vector.retrieve(query, top_k=top_k)
        k = self.keyword.retrieve(query, top_k=top_k)
        return combine_results(v, k, top_k=top_k, alpha=alpha)


def get_retrieval_tool(force_rebuild: bool = False) -> Tuple[RetrievalTool, Dict[str, Any]]:
    faiss_store, bm25_index, chunks, metrics = load_or_build_indexes(
        force_rebuild=force_rebuild
    )
    return RetrievalTool(faiss_store, bm25_index, chunks), metrics