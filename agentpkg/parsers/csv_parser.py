import csv
import io

def parse_csv(content_bytes: bytes) -> str:
    text = content_bytes.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return ""
    header = rows[0]
    formatted_rows = []
    for idx, row in enumerate(rows[1:], start=1):
        pairs = [f"{h}: {val}" for h, val in zip(header, row)]
        formatted_rows.append(f"Fila {idx}: " + ", ".join(pairs))
    return "\n".join(formatted_rows)
