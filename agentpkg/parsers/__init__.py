"""Text extractors for common document formats."""

from pathlib import Path

from agentpkg.parsers.docx_parser import parse_docx, parse_docx_bytes
from agentpkg.parsers.pdf_parser import parse_pdf, parse_pdf_bytes
from agentpkg.parsers.xlsx_parser import parse_xlsx, parse_xlsx_bytes
from agentpkg.parsers.html_parser import parse_html, parse_html_bytes
from agentpkg.parsers.csv_parser import parse_csv, parse_csv_bytes

_TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".xml", ".yaml", ".yml"}


def parse_file(path: Path) -> str:
    """Extract text from a supported document based on its file extension."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix == ".docx":
        return parse_docx(path)
    if suffix == ".xlsx":
        return parse_xlsx(path)
    if suffix in (".html", ".htm"):
        return parse_html(path)
    if suffix == ".csv":
        return parse_csv(path)
    if suffix in _TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8")
    raise ValueError("Unsupported file type: {}".format(suffix or "(no extension)"))


def parse_bytes(data: bytes, filename: str) -> str:
    """Extract text from supported document bytes using the filename extension."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf_bytes(data)
    if suffix == ".docx":
        return parse_docx_bytes(data)
    if suffix == ".xlsx":
        return parse_xlsx_bytes(data)
    if suffix in (".html", ".htm"):
        return parse_html_bytes(data)
    if suffix == ".csv":
        return parse_csv_bytes(data)
    if suffix in _TEXT_SUFFIXES:
        return data.decode("utf-8")
    if b"\0" not in data:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            pass
    raise ValueError("File is binary or not supported as text: {}".format(filename))


__all__ = [
    "parse_bytes",
    "parse_docx",
    "parse_file",
    "parse_pdf",
    "parse_xlsx",
    "parse_html",
    "parse_csv",
]
