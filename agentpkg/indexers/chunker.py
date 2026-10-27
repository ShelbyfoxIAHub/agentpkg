def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append({
            "text": chunk,
            "start": start,
            "end": end
        })
        if end == text_len:
            break
        start += (chunk_size - overlap)

    return chunks
