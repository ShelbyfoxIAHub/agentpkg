from agentpkg.connectors.base import ModelConnector, BaseConnector
from agentpkg.connectors.ollama import OllamaConnector
from agentpkg.connectors.openai import OpenAIConnector

OPENAI_COMPATIBLE_PROVIDERS = {"openai", "vllm", "lmstudio", "groq", "openrouter"}

def get_connector(spec: str) -> ModelConnector:
    if ":" not in spec:
        return OllamaConnector(model=spec)

    provider, model = spec.split(":", 1)
    provider = provider.lower()

    if provider == "ollama":
        return OllamaConnector(model=model)
    elif provider in OPENAI_COMPATIBLE_PROVIDERS:
        return OpenAIConnector(model=model)
    else:
        raise ValueError(f"Proveedor de modelo no soportado: '{provider}'")

__all__ = ["ModelConnector", "BaseConnector", "OllamaConnector", "OpenAIConnector", "get_connector"]
