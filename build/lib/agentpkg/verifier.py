import json
import zipfile
from pathlib import Path
from agentpkg.crypto import compute_bytes_hash

def verify_package_integrity(package_path: Path) -> tuple[bool, list[str]]:
    package_path = Path(package_path)
    errors = []

    if not package_path.exists():
        return False, [f"Package file not found: {package_path}"]

    try:
        with zipfile.ZipFile(package_path, "r") as z:
            if "manifest.json" not in z.namelist():
                return False, ["Missing manifest.json"]

            manifest_bytes = z.read("manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))

            hashes = manifest.get("hashes", {})
            integrity_files = manifest.get("integrity", {}).get("files", {})
            expected_hashes = {**hashes, **integrity_files}

            for name in z.namelist():
                if name.endswith("/") or name == "manifest.json":
                    continue
                
                content = z.read(name)
                computed_hash = compute_bytes_hash(content)
                rel_name = name[5:] if name.startswith("data/") else name
                
                expected = expected_hashes.get(name) or expected_hashes.get(rel_name)
                
                if expected and computed_hash != expected:
                    errors.append(f"Hash mismatch for {name}: expected {expected}, got {computed_hash}")

    except Exception as e:
        return False, [f"Corrupted archive: {str(e)}"]

    return len(errors) == 0, errors
