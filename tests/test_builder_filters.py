import unittest
import tempfile
import shutil
from pathlib import Path
from agentpkg.builder import create_package
from agentpkg.reader import read_package

class TestBuilderFilters(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_pkg = self.test_dir / "test.agentpkg"
        
        # Estructura de archivos de prueba
        self.src_dir = self.test_dir / "src"
        self.src_dir.mkdir()
        
        (self.src_dir / "doc1.txt").write_text("Documento principal", encoding="utf-8")
        (self.src_dir / "temp.tmp").write_text("Temporal", encoding="utf-8")
        (self.src_dir / "secret.log").write_text("Log interno", encoding="utf-8")
        
        # Archivo .agentpkgignore
        (self.src_dir / ".agentpkgignore").write_text("*.log\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_ignore_file_and_exclude_filters(self):
        create_package(
            self.src_dir,
            self.output_pkg,
            exclude_patterns=["*.tmp"]
        )
        
        data = read_package(self.output_pkg)
        file_paths = [f["path"] for f in data.get("files", [])]
        
        # doc1.txt debe estar presente
        self.assertTrue(any("doc1.txt" in p for p in file_paths))
        # *.tmp excluido por parámetro CLI/API
        self.assertFalse(any("temp.tmp" in p for p in file_paths))
        # *.log excluido por .agentpkgignore
        self.assertFalse(any("secret.log" in p for p in file_paths))

if __name__ == "__main__":
    unittest.main()
