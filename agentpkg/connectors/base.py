"""Base class for model connectors in agentpkg."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseConnector(ABC):
    """Abstract base class for LLM and Embedding model connectors."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Send a list of messages (role/content) to the model and return response string."""
        pass

    @abstractmethod
    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate numerical vector embeddings for a list of text strings."""
        pass
