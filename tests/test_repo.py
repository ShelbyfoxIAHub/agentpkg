import unittest
import tempfile
from pathlib import Path
from agentpkg.repo import analyze_repo_languages

class TestRepoModule(unittest.TestCase):
    def test_analyze_repo_languages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            
            # Crear archivos de prueba
            (dir_path / "main.py").write_text("print('Hello agentpkg')", encoding="utf-8")
            (dir_path / "README.md").write_text("# Test Repo", encoding="utf-8")
            
            languages = analyze_repo_languages(dir_path)
            
            self.assertIn("Python", languages)
            self.assertIn("Markdown", languages)

if __name__ == "__main__":
    unittest.main()
