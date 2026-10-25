import unittest
import tempfile
import shutil
from pathlib import Path

from agentpkg.builder import create_package
from agentpkg.verifier import verify_package_integrity
from agentpkg.parsers import parse_bytes


class TestAgentPkg(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.pkg_path = self.test_dir / "test.agentpkg"

        # Crear estructura de prueba
        self.src_dir = self.test_dir / "src"
        self.src_dir.mkdir()
        
        (self.src_dir / "doc.txt").write_text("Hola mundo agentpkg", encoding="utf-8")
        (self.src_dir / "data.csv").write_text("col1,col2\nval1,val2", encoding="utf-8")
        (self.src_dir / "temp.tmp").write_text("Ignorar este archivo", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pack_and_ignore(self):
        manifest = create_package(self.src_dir, self.pkg_path, title="Test Package")
        self.assertEqual(manifest["name"], "Test Package")
        
        # Verificar que el archivo .tmp haya sido ignorado
        entry_paths = manifest["entry_points"]
        self.assertTrue(any("doc.txt" in p for p in entry_paths))
        self.assertTrue(any("data.csv" in p for p in entry_paths))
        self.assertFalse(any("temp.tmp" in p for p in entry_paths))

    def test_verification(self):
        create_package(self.src_dir, self.pkg_path, title="Test Package")
        is_valid, errors = verify_package_integrity(self.pkg_path)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_parsers(self):
        csv_text = parse_bytes(b"A,B\n1,2", "test.csv")
        self.assertIn("Fila 1: A: 1, B: 2", csv_text)

        html_text = parse_bytes(b"<html><body><h1>Titulo</h1></body></html>", "test.html")
        self.assertIn("Titulo", html_text)


if __name__ == "__main__":
    unittest.main()
