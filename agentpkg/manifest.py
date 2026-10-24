"""Semantic metadata (categories, languages, hashes, capabilities) for manifests."""

import hashlib
import mimetypes
from collections import Counter
from pathlib import PurePosixPath
from typing import Callable, Iterable, List, Optional, Sequence

_LANGUAGES = {
    ".py": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp",
    ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".sh": "shell", ".bash": "shell", ".ps1": "powershell",
    ".sql": "sql", ".r": "r", ".lua": "lua", ".scala": "scala", ".dart": "dart",
}
_CATEGORIES = {
    "document": {".md", ".markdown", ".txt", ".rst", ".pdf", ".docx", ".odt", ".rtf",
                 ".epub", ".tex", ".html", ".htm"},
    "data": {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".sqlite", ".db", ".jsonl",
             ".ndjson", ".xml"},
    "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "video": {".mp4", ".mov", ".mkv", ".webm", ".avi"},
    "archive": {".zip", ".tar", ".gz", ".7z", ".tgz"},
    "model": {".onnx", ".gguf", ".safetensors", ".pt", ".pth"},
}
_MEDIA_TYPES = {
    ".md": "text/markdown", ".markdown": "text/markdown", ".txt": "text/plain",
    ".csv": "text/csv", ".json": "application/json", ".jsonl": "application/x-ndjson",
    ".yaml": "application/yaml", ".yml": "application/yaml", ".toml": "application/toml",
    ".html": "text/html", ".xml": "application/xml", ".py": "text/x-python",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
_CAPABILITY_FOR_CATEGORY = {
    "document": "documents", "code": "code", "data": "data", "config": "config",
    "image": "images", "audio": "audio", "video": "video", "skill": "skills",
    "mcp": "mcp-config", "model": "models",
}
MCP_CONFIG_NAMES = ("mcp.json", ".mcp.json")
SKILL_FILE_NAME = "skill.md"


def sha256_stream(stream, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(chunk_size), b""):
        digest.update(chunk)
    return digest.hexdigest()


def classify_file(path: str) -> dict:
    """Return media_type, category and (for code) language for a package path."""
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(path).suffix.lower()
    info = {
        "media_type": _MEDIA_TYPES.get(suffix)
        or mimetypes.guess_type(path)[0]
        or "application/octet-stream"
    }
    if name == SKILL_FILE_NAME:
        info["category"] = "skill"
    elif name in MCP_CONFIG_NAMES:
        info["category"] = "mcp"
    elif suffix in _LANGUAGES:
        info["category"] = "code"
        info["language"] = _LANGUAGES[suffix]
    else:
        info["category"] = next(
            (cat for cat, suffixes in _CATEGORIES.items() if suffix in suffixes),
            "other",
        )
    return info


def file_record(path: str, size: int, sha256: str) -> dict:
    record = {"path": path, "size_bytes": size, "sha256": sha256}
    record.update(classify_file(path))
    return record


def build_manifest_fields(
    records: Sequence[dict],
    read_text: Callable[[str], Optional[str]],
    capabilities: Iterable[str] = (),
    dependencies: Iterable[dict] = (),
) -> dict:
    """Derive the semantic 1.1 manifest sections from file records."""
    from agentpkg.skills import parse_skill_markdown

    languages = Counter(r["language"] for r in records if "language" in r)
    categories = sorted({r["category"] for r in records})
    entry_points: List[dict] = []
    skills: List[dict] = []
    seen_skills = set()
    for record in records:
        path = record["path"]
        name = PurePosixPath(path).name.lower()
        if record["category"] == "skill":
            skill = None
            text = read_text(path)
            if text is not None:
                skill = parse_skill_markdown(text, path)
            if skill is not None and skill.name not in seen_skills:
                seen_skills.add(skill.name)
                entry = {"name": skill.name, "description": skill.description[:1000],
                         "path": path}
                if skill.command:
                    entry["command"] = list(skill.command)
                skills.append(entry)
            entry_points.append({"path": path, "role": "skill"})
        elif record["category"] == "mcp":
            entry_points.append({"path": path, "role": "mcp-config"})
        elif name.startswith("readme."):
            entry_points.append({"path": path, "role": "overview"})
    detected = {_CAPABILITY_FOR_CATEGORY[c] for c in categories if c in _CAPABILITY_FOR_CATEGORY}
    fields = {
        "data_summary": {
            "file_count": len(records),
            "total_size_bytes": sum(r["size_bytes"] for r in records),
            "primary_languages": [
                language for language, _ in sorted(
                    languages.items(), key=lambda item: (-item[1], item[0])
                )[:8]
            ],
            "categories": categories,
        },
        "files": list(records),
        "capabilities": sorted(detected.union(capabilities)),
        "dependencies": list(dependencies),
        "entry_points": entry_points,
    }
    if skills:
        fields["skills"] = skills
    return fields


def parse_dependency(text: str) -> dict:
    """Parse ``kind:name[@version]`` into a manifest dependency entry."""
    kind, separator, rest = text.partition(":")
    if not separator or not rest:
        raise ValueError("Dependency must look like kind:name[@version]: {!r}".format(text))
    name, _, version = rest.partition("@")
    entry = {"kind": kind, "name": name}
    if version:
        entry["version"] = version
    return entry
