"""Document loader for local filesystem."""
from pathlib import Path
from typing import List

from langchain_core.documents import Document


def load_documents(data_dir: str) -> List[Document]:
    """Load all documents from data directory as Document objects."""
    docs_path = Path(data_dir)
    if not docs_path.exists():
        return []

    documents: List[Document] = []
    for file_path in docs_path.iterdir():
        if not (file_path.is_file() and file_path.suffix in [".txt", ".md"]):
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            doc = Document(
                page_content=content,
                metadata={"source": file_path.name}
            )
            documents.append(doc)
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return documents
