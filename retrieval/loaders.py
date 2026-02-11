"""
File-based document loader.
Loads documents from local filesystem.
"""
from pathlib import Path
from typing import List, Dict


def load_documents(data_dir: str) -> List[Dict[str, str]]:
    """
    Load all documents from data directory.
    """
    docs_path = Path(data_dir)
    if not docs_path.exists():
        return []

    documents: List[Dict[str, str]] = []
    for file_path in docs_path.iterdir():
        if not (file_path.is_file() and file_path.suffix in [".txt", ".md"]):
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            documents.append({"source": file_path.name, "text": content})
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    return documents
