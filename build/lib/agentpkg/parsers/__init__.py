from pathlib import Path
from agentpkg.parsers.csv_parser import parse_csv
from agentpkg.parsers.html_parser import parse_html
from agentpkg.parsers.md_parser import parse_md
from agentpkg.parsers.pdf_parser import parse_pdf
from agentpkg.parsers.docx_parser import parse_docx
from agentpkg.parsers.xlsx_parser import parse_xlsx

def parse_bytes(content_bytes: bytes, filename_or_ext: str) -> str:
    ext = Path(filename_or_ext).suffix.lower()
    if ext == ".csv":
        return parse_csv(content_bytes)
    elif ext in [".html", ".htm"]:
        return parse_html(content_bytes)
    elif ext in [".md", ".markdown"]:
        return parse_md(content_bytes)
    elif ext == ".pdf":
        return parse_pdf(content_bytes)
    elif ext in [".docx", ".doc"]:
        return parse_docx(content_bytes)
    elif ext in [".xlsx", ".xls"]:
        return parse_xlsx(content_bytes)
    return content_bytes.decode("utf-8", errors="ignore")

def parse_file(file_path: Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return parse_bytes(path.read_bytes(), path.name)

__all__ = ["parse_bytes", "parse_csv", "parse_html", "parse_md", "parse_pdf", "parse_docx", "parse_xlsx", "parse_file"]
