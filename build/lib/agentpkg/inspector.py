import json
import zipfile
from pathlib import Path

def inspect_package(package_path: Path) -> dict:
    package_path = Path(package_path)
    with zipfile.ZipFile(package_path, "r") as z:
        manifest = {}
        if "manifest.json" in z.namelist():
            manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        files = [name for name in z.namelist() if not name.endswith("/")]
        return {
            "manifest": manifest,
            "files": files
        }
