import json
import hashlib
import zipfile
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

DEFAULT_IGNORE_PATTERNS = [
    ".git*",
    ".venv*",
    "venv*",
    "env*",
    "node_modules*",
    "__pycache__*",
    "*.pyc",
    "*.agentpkg",
    "*.tmp*",
    ".pytest_cache*",
    ".mypy_cache*",
    "dist*",
    "build*",
    "*.egg-info*",
    ".DS_Store",
    "Thumbs.db",
]

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".md": "markdown",
    ".json": "json",
    ".html": "html",
    ".css": "css",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".txt": "text",
    ".csv": "csv",
    ".xlsx": "excel",
    ".docx": "word",
    ".pdf": "pdf",
}

CATEGORY_MAP = {
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".md": "documentation",
    ".txt": "documentation",
    ".json": "data",
    ".yaml": "config",
    ".yml": "config",
    ".csv": "data",
    ".xlsx": "data",
    ".docx": "documentation",
    ".pdf": "documentation",
}

def load_ignore_patterns(source_dir: Path) -> List[str]:
    patterns = list(DEFAULT_IGNORE_PATTERNS)
    ignore_file = source_dir / ".agentpkgignore"
    if ignore_file.exists():
        with open(ignore_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns

def is_path_ignored(rel_path: Path, ignore_patterns: List[str]) -> bool:
    parts = rel_path.parts
    rel_str = rel_path.as_posix()
    
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(rel_path.name, pattern):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False

def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def detect_attributes(rel_path_str: str) -> Tuple[str, str]:
    path_obj = Path(rel_path_str)
    ext = path_obj.suffix.lower()
    
    lang = LANGUAGE_MAP.get(ext, "unknown")
    
    if "tests/" in rel_path_str or "test/" in rel_path_str or path_obj.name.startswith("test_"):
        cat = "tests"
    elif "skills/" in rel_path_str:
        cat = "skills"
    elif "mcp/" in rel_path_str:
        cat = "mcp_config"
    else:
        cat = CATEGORY_MAP.get(ext, "other")
        
    return lang, cat

def create_package(source_dir: Path, output_path: Path, title: str = "") -> None:
    source_dir = source_dir.resolve()
    output_path = output_path.resolve()
    ignore_patterns = load_ignore_patterns(source_dir)

    file_hashes = {}
    primary_languages: Set[str] = set()
    categories: Set[str] = set()
    capabilities: Set[str] = {"read_resources"}
    dependencies: Set[str] = set()

    temp_zip = output_path.with_suffix(".tmp.zip")
    processed_count = 0

    with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                if file_path == temp_zip or file_path == output_path:
                    continue

                rel_path = file_path.relative_to(source_dir)
                if is_path_ignored(rel_path, ignore_patterns):
                    continue

                rel_path_str = rel_path.as_posix()
                target_in_zip = f"data/{rel_path_str}"
                z.write(file_path, target_in_zip)

                file_hashes[target_in_zip] = calculate_sha256(file_path)

                lang, cat = detect_attributes(rel_path_str)
                if lang != "unknown":
                    primary_languages.add(lang)
                if cat != "other":
                    categories.add(cat)
                
                if cat == "skills":
                    capabilities.add("execute_skills")
                if cat == "mcp_config":
                    capabilities.add("mcp_server")
                    dependencies.add("mcp_protocol")

                processed_count += 1

        manifest = {
            "spec_version": "1.0",
            "title": title or source_dir.name,
            "primary_languages": sorted(list(primary_languages)),
            "categories": sorted(list(categories)),
            "hashes": file_hashes,
            "capabilities": sorted(list(capabilities)),
            "dependencies": sorted(list(dependencies))
        }

        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    temp_zip.replace(output_path)
    print(f"⚡ Proceso finalizado. Total de archivos empaquetados: {processed_count}")
