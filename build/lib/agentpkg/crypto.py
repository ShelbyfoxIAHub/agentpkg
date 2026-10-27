import hashlib
from pathlib import Path

def compute_file_hash(file_path: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques para optimizar el uso de memoria."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_bytes_hash(data: bytes) -> str:
    """Calcula el hash SHA-256 a partir de un flujo de bytes."""
    return hashlib.sha256(data).hexdigest()
