from typing import List, Dict, Any

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Divide un texto largo en fragmentos más pequeños con un nivel de solape."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    return chunks
