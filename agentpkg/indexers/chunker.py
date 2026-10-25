"""Text chunker module for agentpkg indexers."""

from typing import List, Dict, Any


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Splits text into chunks of specified character size with overlap.
    Returns a list of dicts with chunk text and metadata.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_str = text[start:end]
        chunks.append({
            "text": chunk_str,
            "start": start,
            "end": end,
        })

        if end == text_len:
            break

        start += chunk_size - overlap

    return chunks
