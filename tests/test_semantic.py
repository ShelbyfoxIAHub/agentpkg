import unittest
from pathlib import Path
from agentpkg.builder import detect_file_metadata

class TestSemanticMetadata(unittest.TestCase):
    def test_semantic_category_detection(self):
        sample_files = [
            Path("skills/web_search.py"),
            Path("config/mcp.json"),
            Path("data/sales.csv"),
            Path("storage/app.db"),
            Path("vectors/index.hnsw"),
            Path("graphs/knowledge.ttl"),
            Path("docs/readme.md"),
        ]
        
        languages, categories = detect_file_metadata(sample_files)
        
        self.assertIn("Python", languages)
        self.assertIn("skill", categories)
        self.assertIn("config_mcp", categories)
        self.assertIn("dataset", categories)
        self.assertIn("database", categories)
        self.assertIn("vector", categories)
        self.assertIn("graph", categories)
        self.assertIn("document", categories)

if __name__ == "__main__":
    unittest.main()
