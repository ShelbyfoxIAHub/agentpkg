"""Package integrity and manifest validation."""

import json
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Tuple


def verify_package_integrity(package_path: str) -> Tuple[bool, List[str]]:
    """
    Verify the SHA-256 integrity of all files inside an .agentpkg package.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    
    with zipfile.ZipFile(package_path, "r") as zip_ref:
        if "manifest.json" not in zip_ref.namelist():
            return False, ["Error: El paquete no contiene manifest.json."]

        manifest_data = json.loads(zip_ref.read("manifest.json").decode("utf-8"))
        integrity_info = manifest_data.get("integrity", {})
        expected_hashes = integrity_info.get("files", {})

        if not expected_hashes:
            return False, ["Advertencia: El manifiesto no contiene registros de integridad SHA-256."]

        for file_path, expected_hash in expected_hashes.items():
            if file_path not in zip_ref.namelist():
                errors.append(f"Falta el archivo: '{file_path}'")
                continue

            file_bytes = zip_ref.read(file_path)
            actual_hash = hashlib.sha256(file_bytes).hexdigest()

            if actual_hash != expected_hash:
                errors.append(f"Hash no coincide en '{file_path}': esperado {expected_hash[:8]}..., real {actual_hash[:8]}...")

    is_valid = len(errors) == 0
    return is_valid, errors
