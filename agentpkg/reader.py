import base64
import json
import zipfile
from pathlib import Path
from agentpkg.parsers import parse_bytes

def read_package(package_path: Path) -> dict:
    package_path = Path(package_path)
    files = []
    manifest_data = {}

    binary_extensions = {".dat", ".bin", ".pdf", ".docx", ".xlsx", ".png", ".jpg", ".zip", ".pyc", ".db", ".hnsw"}

    with zipfile.ZipFile(package_path, "r") as z:
        for name in z.namelist():
            if name == "manifest.json":
                try:
                    manifest_data = json.loads(z.read(name).decode("utf-8"))
                except Exception:
                    manifest_data = {}
            elif name.startswith("data/") and not name.endswith("/"):
                data = z.read(name)
                ext = Path(name).suffix.lower()

                if ext in binary_extensions or b"\x00" in data:
                    b64_content = base64.b64encode(data).decode("ascii")
                    files.append({
                        "path": name,
                        "encoding": "base64",
                        "content": b64_content,
                        "text_extraction": {
                            "available": False,
                            "error": "Binary or unsupported document format"
                        }
                    })
                else:
                    try:
                        text_content = parse_bytes(data, name)
                        files.append({
                            "path": name,
                            "encoding": "utf-8",
                            "content": text_content,
                            "text_extraction": {
                                "available": True
                            }
                        })
                    except Exception as e:
                        b64_content = base64.b64encode(data).decode("ascii")
                        files.append({
                            "path": name,
                            "encoding": "base64",
                            "content": b64_content,
                            "text_extraction": {
                                "available": False,
                                "error": str(e)
                            }
                        })

    return {
        "format": "agentpkg.read/1",
        "manifest": manifest_data,
        "files": files
    }
