"""Character-based document chunking (minimal)."""
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_CHARS


def chunk_documents(
    docs: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Split documents into chunks with minimal metadata."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be less than chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    raw_chunks = splitter.split_documents(docs)

    per_source_counter = {}
    kept: List[Document] = []

    for c in raw_chunks:
        src = c.metadata.get("source", "unknown")

        if len((c.page_content or "").strip()) < MIN_CHUNK_CHARS:
            continue

        idx = per_source_counter.get(src, 0)
        per_source_counter[src] = idx + 1

        c.metadata = {
            **c.metadata,
            "chunk_index": idx,
            "chunk_id": f"{src}::chunk_{idx}",
        }

        kept.append(c)

    return kept


def documents_to_dicts(doc_chunks: List[Document]) -> List[Dict[str, Any]]:
    """Convert Document chunks to dict format."""
    result: List[Dict[str, Any]] = []
    
    for doc in doc_chunks:
        chunk_dict = {
            "text": doc.page_content,
            **doc.metadata,
        }
        result.append(chunk_dict)
    
    return result
