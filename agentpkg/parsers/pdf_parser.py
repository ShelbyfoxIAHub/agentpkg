"""PDF text extraction."""

from pathlib import Path
from io import BytesIO


def parse_pdf(path: Path) -> str:
    """Return text from every page in a PDF file."""
    return parse_pdf_bytes(Path(path).read_bytes())


def parse_pdf_bytes(data: bytes) -> str:
    """Return text from every page in PDF bytes."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError(
            "PDF parsing requires the optional dependencies; install "
            "'agentpkg[documents]'."
        ) from error

    reader = PdfReader(BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)
