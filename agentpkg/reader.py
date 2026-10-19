"""Provider-neutral package reading for local and hosted AI integrations."""

import base64
import mimetypes
import zlib
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from agentpkg.loader import _read_package
from agentpkg.parsers import parse_bytes


def read_package(package: Path) -> dict:
    """Read package contents into a JSON-serializable, provider-neutral payload.

    UTF-8 text is returned as text. Other file contents are base64 encoded so
    applications can pass original bytes to a compatible model or API.
    """
    manifest, members = _read_package(package)
    files = []
    with ZipFile(Path(package).expanduser(), "r") as archive:
        for member in members:
            if member.is_dir() or member.filename == "manifest.json":
                continue
            try:
                data = archive.read(member)
            except (BadZipFile, RuntimeError, zlib.error) as error:
                raise ValueError(
                    "Package data is corrupted or unreadable: {}".format(
                        member.filename
                    )
                ) from error
            record = {
                "path": member.filename,
                "media_type": mimetypes.guess_type(member.filename)[0]
                or "application/octet-stream",
                "size_bytes": len(data),
            }
            try:
                text = parse_bytes(data, Path(member.filename).name)
            except RuntimeError as error:
                record["encoding"] = "base64"
                record["content"] = base64.b64encode(data).decode("ascii")
                record["text_extraction"] = {
                    "available": False,
                    "reason": str(error),
                }
            except ValueError:
                record["encoding"] = "base64"
                record["content"] = base64.b64encode(data).decode("ascii")
            else:
                if Path(member.filename).suffix.lower() in {".pdf", ".docx", ".xlsx"}:
                    record["encoding"] = "base64"
                    record["content"] = base64.b64encode(data).decode("ascii")
                    record["extracted_text"] = text
                else:
                    record["encoding"] = "utf-8"
                    record["content"] = text
            files.append(record)

    return {
        "format": "agentpkg.read/1",
        "manifest": manifest,
        "files": files,
    }
