import unittest
from agentpkg.connectors import get_connector, OllamaConnector, OpenAIConnector

class TestConnectors(unittest.TestCase):
    def test_factory_ollama(self):
        connector = get_connector("ollama:llama3")
        self.assertIsInstance(connector, OllamaConnector)
        self.assertEqual(connector.model, "llama3")

    def test_factory_default_provider(self):
        connector = get_connector("llama3")
        self.assertIsInstance(connector, OllamaConnector)
        self.assertEqual(connector.model, "llama3")

    def test_factory_openai_compatible(self):
        connector = get_connector("vllm:llama-3-70b")
        self.assertIsInstance(connector, OpenAIConnector)
        self.assertEqual(connector.model, "llama-3-70b")

    def test_factory_invalid_provider(self):
        with self.assertRaises(ValueError):
            get_connector("unsupported_provider:model")

if __name__ == "__main__":
    unittest.main()
