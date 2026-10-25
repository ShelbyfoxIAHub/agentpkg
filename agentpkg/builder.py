"""Creation of agentpkg archives."""

import fnmatch
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple, Set
from zipfile import ZIP_DEFLATED, ZipFile

from agentpkg import SPEC_VERSION

DEFAULT_IGNORE_PATTERNS = [
    ".git*",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".venv",
    "venv",
    ".env",
    ".DS_Store",
    "Thumbs.db",
    "*.tmp",
    "*.agentpkg",
]


def load_ignore_patterns(source_dir: Path) -> List[str]:
    """Load ignore patterns from default list and .agentpkgignore file if present."""
    patterns = list(DEFAULT_IGNORE_PATTERNS)
    ignore_file = source_dir / ".agentpkgignore"
    if ignore_file.exists() and ignore_file.is_file():
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            pass
    return patterns


def is_ignored(path: Path, source_dir: Path, patterns: List[str]) -> bool:
    """Check if a file or directory relative to source_dir matches any ignore pattern."""
    rel_path = path.relative_to(source_dir).as_posix()
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
        # Match directory name inside path parts
        if any(fnmatch.fnmatch(part, pattern) for part in path.parts):
            return True
    return False


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def detect_file_metadata(files: List[Path]) -> Tuple[List[str], List[str]]:
    """Detect primary languages and categories based on file path and extensions."""
    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".html": "HTML",
        ".css": "CSS",
        ".sh": "Shell",
        ".bash": "Shell",
        ".ps1": "PowerShell",
        ".c": "C",
        ".cpp": "C++",
        ".java": "Java",
        ".rs": "Rust",
        ".go": "Go",
    }

    languages: Set[str] = set()
    categories: Set[str] = set()

    for path in files:
        name_lower = path.name.lower()
        ext = path.suffix.lower()
        parts_lower = [p.lower() for p in path.parts]

        # Detect programming languages
        if ext in lang_map:
            languages.add(lang_map[ext])

        # Detect categories semantically
        if name_lower.endswith(".mcp.json") or name_lower == "mcp.json" or "mcp" in parts_lower:
            categories.add("config_mcp")
        elif "skills" in parts_lower or name_lower.endswith(".skill.json") or name_lower.endswith(".skill.py"):
            categories.add("skill")
        elif ext in [".csv", ".tsv", ".parquet", ".jsonl"]:
            categories.add("dataset")
        elif ext in [".db", ".sqlite", ".sqlite3", ".duckdb"]:
            categories.add("database")
        elif ext in [".index", ".vec", ".hnsw"]:
            categories.add("vector")
        elif ext in [".graphml", ".gexf", ".ttl", ".rdf"]:
            categories.add("graph")
        elif ext in [".py", ".js", ".ts", ".sh", ".bash", ".ps1", ".c", ".cpp", ".java", ".rs", ".go"]:
            categories.add("code")
        elif ext in [".json", ".yaml", ".yml", ".toml", ".ini"]:
            categories.add("config")
        elif ext in [".md", ".txt", ".pdf", ".docx", ".xlsx", ".rst", ".html"]:
            categories.add("document")

    return sorted(list(languages)), sorted(list(categories))


def create_package(
    source: Path,
    destination: Path,
    title: Optional[str] = None,
    description: str = "",
    author: str = "",
) -> dict:
    """Package the files in a directory and return the generated manifest."""
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError("Source directory does not exist: {}".format(source))
    if not source.is_dir():
        raise NotADirectoryError("Source path is not a directory: {}".format(source))

    ignore_patterns = load_ignore_patterns(source)

    files = []
    directories = []
    temporary = destination.with_name(destination.name + ".tmp")
    for candidate in source.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(
                "Symbolic links are not supported in source directories: {}".format(
                    candidate
                )
            )
        if is_ignored(candidate, source, ignore_patterns):
            continue

        if candidate.is_dir():
            directories.append(candidate)
        elif candidate.is_file():
            resolved = candidate.resolve()
            if resolved in (destination, temporary):
                continue
            files.append(candidate)

    files.sort(key=lambda path: path.relative_to(source).as_posix().casefold())
    directories.sort(
        key=lambda path: path.relative_to(source).as_posix().casefold()
    )
    if not files:
        raise ValueError("Source directory contains no regular files: {}".format(source))

    data_paths = [
        "data/{}".format(path.relative_to(source).as_posix()) for path in files
    ]
    data_directories = [
        "data/{}/".format(path.relative_to(source).as_posix())
        for path in directories
    ]

    file_hashes = {}
    for path, archive_path in zip(files, data_paths):
        file_hashes[archive_path] = calculate_sha256(path)

    languages, categories = detect_file_metadata(files)

    manifest = {
        "spec_version": SPEC_VERSION,
        "name": title or source.name,
        "description": description,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data_summary": {
            "file_count": len(files),
            "primary_languages": languages,
            "categories": categories,
        },
        "capabilities": [],
        "dependencies": {},
        "entry_points": data_paths,
        "integrity": {
            "algorithm": "sha256",
            "files": file_hashes,
        },
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            )
            archive.writestr("data/", b"")
            for archive_path in data_directories:
                archive.writestr(archive_path, b"")
            for path, archive_path in zip(files, data_paths):
                archive.write(path, archive_path)
        os.replace(str(temporary), str(destination))
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    return manifest
