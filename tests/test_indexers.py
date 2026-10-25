import unittest
from agentpkg.indexers.chunker import chunk_text
from agentpkg.indexers.vector_index import SimpleVectorIndex, cosine_similarity
from agentpkg.connectors.base import BaseConnector

class MockConnector(BaseConnector):
    """Mock connector returning deterministic dummy vectors for testing."""
    def chat(self, messages, **kwargs):
        return "mock response"

    def embed(self, texts, **kwargs):
        # Generates simple dummy 3D vectors based on text length
        embeddings = []
        for t in texts:
            val = float(len(t))
            embeddings.append([val, val * 0.5, 1.0])
        return embeddings

class TestIndexers(unittest.TestCase):
    def test_chunk_text_basic(self):
        text = "Hello world. This is a simple test text for chunking."
        chunks = chunk_text(text, chunk_size=20, overlap=5)
        self.assertTrue(len(chunks) > 1)
        self.assertEqual(chunks[0]["start"], 0)

    def test_chunk_text_empty(self):
        self.assertEqual(chunk_text(""), [])

    def test_cosine_similarity(self):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        vec_c = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_b), 1.0)
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_c), 0.0)

    def test_vector_index_build_and_search(self):
        docs = [
            {"file_path": "doc1.txt", "content": "Python programming language for AI."},
            {"file_path": "doc2.txt", "content": "Cooking recipes and kitchen tools."},
        ]
        mock = MockConnector()
        index = SimpleVectorIndex()
        index.build_from_documents(docs, mock, chunk_size=100)

        self.assertTrue(len(index.entries) >= 2)
        
        # Test query search
        query_vec = [10.0, 5.0, 1.0]
        results = index.search(query_vec, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("file_path", results[0])
        self.assertIn("score", results[0])

if __name__ == "__main__":
    unittest.main()
