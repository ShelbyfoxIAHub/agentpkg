"""Model connectors factory and public interface for agentpkg."""

from agentpkg.connectors.base import BaseConnector
from agentpkg.connectors.ollama import OllamaConnector
from agentpkg.connectors.openai import OpenAIConnector


def get_connector(model_spec: str) -> BaseConnector:
    """
    Factory function to instantiate a model connector.
    
    Examples:
        - "ollama:llama3" -> OllamaConnector(model="llama3")
        - "openai:gpt-4o" -> OpenAIConnector(model="gpt-4o")
        - "llama3" (default provider is ollama) -> OllamaConnector(model="llama3")
    """
    if ":" in model_spec:
        provider, model_name = model_spec.split(":", 1)
    else:
        provider, model_name = "ollama", model_spec

    provider = provider.lower()

    if provider == "ollama":
        return OllamaConnector(model=model_name)
    elif provider in ("openai", "vllm", "lmstudio", "groq"):
        return OpenAIConnector(model=model_name)
    else:
        raise ValueError(f"Unsupported model provider: '{provider}' in spec '{model_spec}'")


__all__ = ["BaseConnector", "OllamaConnector", "OpenAIConnector", "get_connector"]
