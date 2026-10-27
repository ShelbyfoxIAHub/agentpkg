def parse_md(content_bytes: bytes) -> str:
    """Extrae texto de contenido Markdown en bytes."""
    return content_bytes.decode("utf-8", errors="ignore")
