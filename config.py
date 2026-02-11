"""Configuration settings for the agentic assistant."""
import os
from pathlib import Path

DATA_DIR = os.getenv("DATA_DIR", "data/sample_docs")
INDEX_DIR = os.getenv("INDEX_DIR", "data/.index")

RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")
MIN_TOP_K = int(os.getenv("MIN_TOP_K", "4"))
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "12"))
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.7"))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
MIN_CHUNK_CHARS = int(os.getenv("MIN_CHUNK_CHARS", "40"))

WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4o-mini")
MAX_WRITER_PROMPT_TOKENS = int(os.getenv("MAX_WRITER_PROMPT_TOKENS", "6000"))

Path(INDEX_DIR).mkdir(parents=True, exist_ok=True)
