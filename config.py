"""
Configuration settings for the agentic assistant.
Can be overridden via environment variables.
"""
import os
from pathlib import Path

DATA_DIR = os.getenv("DATA_DIR", "data/sample_docs")
INDEX_DIR = os.getenv("INDEX_DIR", "data/.index")

TOP_K = int(os.getenv("TOP_K", "4"))
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.7"))
MAX_EXHAUSTIVE_CHUNKS = int(os.getenv("MAX_EXHAUSTIVE_CHUNKS", "60"))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4o-mini")
MAX_WRITER_PROMPT_TOKENS = int(os.getenv("MAX_WRITER_PROMPT_TOKENS", "6000"))

Path(INDEX_DIR).mkdir(parents=True, exist_ok=True)
