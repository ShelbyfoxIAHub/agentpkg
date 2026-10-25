import base64
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from agentpkg.builder import create_package
from agentpkg.cli import main
from agentpkg.loader import inspect_package, unpack_package
from agentpkg.parsers import parse_file
from agentpkg.reader import read_package


class AgentPackageTests(unittest.TestCase):
    def test_create_inspect_and_unpack_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "documents"
            (source / "notes").mkdir(parents=True)
            (source / "empty" / "nested").mkdir(parents=True)
            (source / "readme.md").write_text("hello\n", encoding="utf-8")
            (source / "notes" / "guide.txt").write_text("guide\n", encoding="utf-8")
            package = root / "knowledge.agentpkg"

            manifest = create_package(
                source,
                package,
                title="Knowledge",
                description="Local documents",
                author="Test",
            )
            inspected = inspect_package(package)

            self.assertEqual(manifest["name"], "Knowledge")
            self.assertEqual(manifest["data_summary"]["file_count"], 2)
            self.assertEqual(
                set(inspected["files"]),
                {
                    "manifest.json",
                    "data/readme.md",
                    "data/notes/guide.txt",
                },
            )
            with ZipFile(package) as archive:
                self.assertIn("data/", archive.namelist())
                self.assertIn("data/empty/nested/", archive.namelist())
            self.assertEqual(inspected["manifest"], manifest)

            destination = root / "extracted"
            extracted = unpack_package(package, destination)
            self.assertEqual(len(extracted), 3)
            self.assertEqual(
                (destination / "data" / "notes" / "guide.txt").read_text(
                    encoding="utf-8"
                ),
                "guide\n",
            )

    def test_unpack_refuses_to_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "file.txt").write_text("content\n", encoding="utf-8")
            package = root / "package.agentpkg"
            create_package(source, package)

            destination = root / "destination"
            destination.mkdir()
            (destination / "data" / "file.txt").mkdir(parents=True)

            with self.assertRaises(FileExistsError):
                unpack_package(package, destination)

    def test_package_preserves_arbitrary_agent_and_data_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "agent_project"
            source.mkdir()
            (source / "agent.py").write_text("print('agent')", encoding="utf-8")
            (source / "config.json").write_text('{"key": "value"}', encoding="utf-8")
            (source / "data.csv").write_text("a,b,c\n1,2,3", encoding="utf-8")

            package = root / "knowledge" / "knowledge.agentpkg"
            manifest = create_package(source, package)

            inspected = inspect_package(package)
            self.assertEqual(
                set(inspected["files"]),
                {
                    "manifest.json",
                    "data/agent.py",
                    "data/config.json",
                    "data/data.csv",
                },
            )
            self.assertEqual(manifest["data_summary"]["file_count"], 3)

    def test_reader_exposes_text_and_lossless_binary_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "doc.md").write_bytes(b"# Heading\nBody text")
            (source / "binary.dat").write_bytes(b"\x00\x01\x02\x03")

            package = root / "context.agentpkg"
            create_package(source, package)

            payload = read_package(package)
            self.assertEqual(payload["format"], "agentpkg.read/1")
            self.assertEqual(len(payload["files"]), 2)

            files_by_path = {f["path"]: f for f in payload["files"]}
            md_file = files_by_path["data/doc.md"]
            self.assertEqual(md_file["encoding"], "utf-8")
            self.assertEqual(md_file["content"], "# Heading\nBody text")

            bin_file = files_by_path["data/binary.dat"]
            self.assertEqual(bin_file["encoding"], "base64")
            self.assertEqual(
                base64.b64decode(bin_file["content"]), b"\x00\x01\x02\x03"
            )

    def test_read_cli_writes_provider_neutral_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "note.txt").write_text("hello reader", encoding="utf-8")

            package = root / "context.agentpkg"
            create_package(source, package)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["read", str(package)])

            data = json.loads(output.getvalue())
            self.assertEqual(data["format"], "agentpkg.read/1")
            self.assertEqual(data["files"][0]["path"], "data/note.txt")

    def test_reader_reports_when_optional_document_parser_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "document.pdf").write_bytes(b"%PDF-binary")
            package = root / "context.agentpkg"
            create_package(source, package)

            with patch(
                "agentpkg.reader.parse_bytes",
                side_effect=RuntimeError("install agentpkg[documents]"),
            ):
                file_record = read_package(package)["files"][0]

            self.assertEqual(file_record["encoding"], "base64")
            self.assertEqual(
                base64.b64decode(file_record["content"]),
                b"%PDF-binary",
            )
            self.assertFalse(file_record["text_extraction"]["available"])

    def test_manifest_phase_1_integrity_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "script.py").write_bytes(b"print('hello')\n")
            (source / "readme.md").write_bytes(b"# Title\n")
            package = root / "test.agentpkg"

            manifest = create_package(source, package)

            self.assertIn("integrity", manifest)
            self.assertEqual(manifest["integrity"]["algorithm"], "sha256")
            self.assertIn("data/script.py", manifest["integrity"]["files"])
            self.assertIn("data/readme.md", manifest["integrity"]["files"])
            self.assertEqual(len(manifest["integrity"]["files"]["data/script.py"]), 64)

            self.assertEqual(manifest["data_summary"]["primary_languages"], ["Python"])
            self.assertEqual(
                manifest["data_summary"]["categories"], ["code", "document"]
            )
            self.assertEqual(manifest["capabilities"], [])
            self.assertEqual(manifest["dependencies"], {})


if __name__ == "__main__":
    unittest.main()
