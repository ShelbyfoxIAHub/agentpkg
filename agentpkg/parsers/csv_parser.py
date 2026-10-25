"""CSV text extractor converting tabular data into semantic sentences."""

import csv
import io


def parse_csv_bytes(data: bytes) -> str:
    """Convert CSV bytes into descriptive textual sentences."""
    text = data.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return ""

    header = rows[0]
    lines = []
    for idx, row in enumerate(rows[1:], 1):
        row_str = ", ".join(f"{h}: {val}" for h, val in zip(header, row) if val.strip())
        if row_str:
            lines.append(f"Fila {idx}: {row_str}")

    return "\n".join(lines)


def parse_csv(file_path) -> str:
    """Extract clean text from CSV file."""
    with open(file_path, "rb") as f:
        return parse_csv_bytes(f.read())
