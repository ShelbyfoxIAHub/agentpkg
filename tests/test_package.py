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
            self.assertTrue((destination / "data" / "empty" / "nested").is_dir())

    def test_unpack_refuses_to_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "file.txt").write_text("package", encoding="utf-8")
            package = root / "package.agentpkg"
            create_package(source, package)

            destination = root / "destination"
            existing = destination / "data" / "file.txt"
            existing.parent.mkdir(parents=True)
            existing.write_text("keep", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                unpack_package(package, destination)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep")

    def test_inspect_rejects_archive_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "unsafe.agentpkg"
            manifest = {
                "spec_version": "1.0",
                "name": "unsafe",
            }
            with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("../outside.txt", "unsafe")

            with self.assertRaisesRegex(ValueError, "Unsafe path"):
                inspect_package(package)

    def test_inspect_rejects_noncanonical_archive_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            for unsafe_name in ("data//file.txt", "data/./file.txt"):
                package = Path(temporary) / "unsafe.agentpkg"
                with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                    archive.writestr(
                        "manifest.json",
                        json.dumps({"spec_version": "1.0", "name": "unsafe"}),
                    )
                    archive.writestr("data/", b"")
                    archive.writestr(unsafe_name, "unsafe")

                with self.subTest(name=unsafe_name):
                    with self.assertRaisesRegex(ValueError, "Unsafe path"):
                        inspect_package(package)

    def test_inspect_rejects_nonportable_windows_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            for unsafe_name in (
                "data/NUL.txt",
                "data/trailing.",
                "data/question?.txt",
            ):
                package = Path(temporary) / "nonportable.agentpkg"
                with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                    archive.writestr(
                        "manifest.json",
                        json.dumps({"spec_version": "1.0", "name": "nonportable"}),
                    )
                    archive.writestr("data/", b"")
                    archive.writestr(unsafe_name, "unsafe")

                with self.subTest(name=unsafe_name):
                    with self.assertRaisesRegex(ValueError, "Non-portable path"):
                        inspect_package(package)

    def test_inspect_rejects_file_directory_path_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "conflict.agentpkg"
            with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                archive.writestr(
                    "manifest.json",
                    json.dumps({"spec_version": "1.0", "name": "conflict"}),
                )
                archive.writestr("data/", b"")
                archive.writestr("data/item", "file")
                archive.writestr("data/item/child.txt", "child")

            with self.assertRaisesRegex(ValueError, "conflicts with a file"):
                inspect_package(package)

    def test_inspect_rejects_case_colliding_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "case-collision.agentpkg"
            with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                archive.writestr(
                    "manifest.json",
                    json.dumps({"spec_version": "1.0", "name": "collision"}),
                )
                archive.writestr("data/", b"")
                archive.writestr("data/Notes.txt", "first")
                archive.writestr("data/notes.txt", "second")

            with self.assertRaisesRegex(ValueError, "case-colliding paths"):
                inspect_package(package)

    def test_inspect_requires_data_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "missing-data.agentpkg"
            manifest = {"spec_version": "1.0", "name": "missing-data"}
            with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(manifest))

            with self.assertRaisesRegex(ValueError, "missing the required data/"):
                inspect_package(package)

    def test_empty_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "empty"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "no regular files"):
                create_package(source, root / "empty.agentpkg")

    def test_parse_file_reads_utf8_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            text_file = Path(temporary) / "notes.md"
            text_file.write_text("contexto\n", encoding="utf-8")
            self.assertEqual(parse_file(text_file), "contexto\n")

    def test_parse_file_rejects_unknown_extensions(self):
        with self.assertRaisesRegex(ValueError, "Unsupported file type"):
            parse_file(Path("archive.bin"))

    def test_package_preserves_arbitrary_agent_and_data_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "knowledge"
            source.mkdir()
            arbitrary_files = {
                "review.skill": b"skill definition",
                "server.mcp": b'{"tools": []}',
                "embeddings.vector": b"\x00\x01\xfe",
                "relations.graph": b"node-a -> node-b",
            }
            for name, contents in arbitrary_files.items():
                (source / name).write_bytes(contents)

            package = source / "knowledge.agentpkg"
            manifest = create_package(source, package)

            self.assertEqual(manifest["data_summary"]["file_count"], 4)
            destination = root / "unpacked"
            unpack_package(package, destination)
            for name, contents in arbitrary_files.items():
                self.assertEqual(
                    (destination / "data" / name).read_bytes(),
                    contents,
                )
            self.assertNotIn(
                "data/knowledge.agentpkg",
                inspect_package(package)["files"],
            )

    def test_reader_exposes_text_and_lossless_binary_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "instructions.skill").write_text(
                "Use local context.", encoding="utf-8"
            )
            binary = b"\x00\x01\xff\x10"
            (source / "vectors.bin").write_bytes(binary)
            package = root / "context.agentpkg"
            create_package(source, package)

            context = read_package(package)
            files = {item["path"]: item for item in context["files"]}

            self.assertEqual(context["format"], "agentpkg.read/1")
            self.assertEqual(
                files["data/instructions.skill"]["content"],
                "Use local context.",
            )
            self.assertEqual(files["data/instructions.skill"]["encoding"], "utf-8")
            self.assertEqual(files["data/vectors.bin"]["encoding"], "base64")
            self.assertEqual(
                base64.b64decode(files["data/vectors.bin"]["content"]),
                binary,
            )
            json.dumps(context, ensure_ascii=False)

    def test_read_cli_writes_provider_neutral_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "facts.txt").write_text("local fact", encoding="utf-8")
            package = root / "context.agentpkg"
            output = root / "context.json"
            create_package(source, package)

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    ["read", str(package), "--output", str(output)]
                )

            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(result["files"][0]["content"], "local fact")

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


if __name__ == "__main__":
    unittest.main()
