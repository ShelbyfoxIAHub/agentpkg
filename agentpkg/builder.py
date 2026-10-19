"""Creation of agentpkg archives."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

from agentpkg import SPEC_VERSION


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
    manifest = {
        "spec_version": SPEC_VERSION,
        "name": title or source.name,
        "description": description,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data_summary": {
            "file_count": len(files),
            "primary_languages": [],
            "categories": [],
        },
        "entry_points": data_paths,
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
