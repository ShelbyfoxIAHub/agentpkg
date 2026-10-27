from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ModelConnector(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Envía el historial de conversación al modelo y retorna la respuesta."""
        pass

    @abstractmethod
    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Genera representaciones en vectores (embeddings) para una lista de textos."""
        pass

# Alias de compatibilidad
BaseConnector = ModelConnector
