"""Inspection and safe extraction of agentpkg archives."""

import json
import os
import stat
import zlib
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
}.union(
    {"COM{}".format(index) for index in range(1, 10)},
    {"LPT{}".format(index) for index in range(1, 10)},
)


def _safe_member_path(name: str, is_dir: bool = False) -> PurePosixPath:
    path_name = name[:-1] if is_dir and name.endswith("/") else name
    path = PurePosixPath(path_name)
    raw_parts = path_name.split("/")
    if (
        not name
        or path.is_absolute()
        or "\\" in name
        or ":" in name
        or any(part in ("", ".", "..") for part in raw_parts)
    ):
        raise ValueError("Unsafe path in package: {!r}".format(name))
    for part in raw_parts:
        windows_stem = part.split(".", 1)[0].upper()
        if (
            part.endswith((" ", "."))
            or windows_stem in _WINDOWS_RESERVED_NAMES
            or any(ord(character) < 32 or character in '<>:"|?*' for character in part)
        ):
            raise ValueError("Non-portable path in package: {!r}".format(name))
    return path


def _read_package(package: Path):
    package = Path(package).expanduser()
    try:
        archive = ZipFile(package, "r")
    except (BadZipFile, OSError) as error:
        raise ValueError("Not a readable agentpkg archive: {}".format(package)) from error

    with archive:
        members = archive.infolist()
        paths = {}
        for member in members:
            path = _safe_member_path(member.filename, member.is_dir())
            normalized = path.as_posix()
            canonical = normalized.casefold()
            if canonical in paths:
                raise ValueError(
                    "Package contains duplicate or case-colliding paths: {}".format(
                        member.filename
                    )
                )
            paths[canonical] = (normalized, member.is_dir())

            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(
                    "Symbolic links are not allowed in packages: {}".format(
                        member.filename
                    )
                )

            top_level = path.parts[0]
            if normalized == "manifest.json":
                if member.is_dir():
                    raise ValueError("manifest.json must be a file")
            elif top_level not in ("data", "index"):
                raise ValueError(
                    "Unexpected path outside data/ or index/: {}".format(
                        member.filename
                    )
                )
            elif normalized in ("data", "index") and not member.is_dir():
                raise ValueError("{} must be a directory".format(normalized))

        if "manifest.json" not in paths:
            raise ValueError("Package is missing manifest.json")
        manifest_info = next(
            member for member in members if member.filename == "manifest.json"
        )
        if manifest_info.file_size > 1024 * 1024:
            raise ValueError("manifest.json exceeds the 1 MiB size limit")
        if not any(
            name == "data" or name.startswith("data/")
            for name, _ in paths.values()
        ):
            raise ValueError("Package is missing the required data/ directory")

        for normalized, is_dir in paths.values():
            parts = normalized.split("/")
            for index in range(1, len(parts)):
                parent = "/".join(parts[:index])
                parent_entry = paths.get(parent.casefold())
                if parent_entry is not None and not parent_entry[1]:
                    raise ValueError(
                        "Package path conflicts with a file: {}".format(parent)
                    )

        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (BadZipFile, RuntimeError, zlib.error) as error:
            raise ValueError("Package manifest data is corrupted or unreadable") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Package has an invalid manifest.json") from error
        if not isinstance(manifest, dict):
            raise ValueError("manifest.json must contain a JSON object")
        if not isinstance(manifest.get("spec_version"), str):
            raise ValueError("manifest.json is missing a valid spec_version")
        if not isinstance(manifest.get("name"), str):
            raise ValueError("manifest.json is missing a valid name")
        return manifest, members


def inspect_package(package: Path) -> dict:
    """Return the manifest and archive file list for a package."""
    manifest, members = _read_package(package)
    return {
        "manifest": manifest,
        "files": [member.filename for member in members if not member.is_dir()],
    }


def unpack_package(package: Path, destination: Path) -> list:
    """Extract a package without allowing path traversal or overwrites."""
    package = Path(package).expanduser()
    destination = Path(destination).expanduser().resolve()
    manifest, members = _read_package(package)
    del manifest

    entries = members
    targets = []
    for member in entries:
        relative = _safe_member_path(member.filename, member.is_dir())
        target = (destination / Path(*relative.parts)).resolve()
        try:
            target.relative_to(destination)
        except ValueError as error:
            raise ValueError(
                "Package path escapes the destination: {}".format(member.filename)
            ) from error
        if target.exists() and (
            not member.is_dir() or not target.is_dir()
        ):
            raise FileExistsError("Refusing to overwrite existing path: {}".format(target))
        targets.append((member, target))

    with ZipFile(package, "r") as archive:
        for member, target in targets:
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
        for member, target in targets:
            if member.is_dir():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with archive.open(member, "r") as source, target.open("xb") as output:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
            except (BadZipFile, RuntimeError, zlib.error) as error:
                if target.exists():
                    target.unlink()
                raise ValueError(
                    "Package data is corrupted or unreadable: {}".format(
                        member.filename
                    )
                ) from error

    return [
        str(target) for member, target in targets if not member.is_dir()
    ]
