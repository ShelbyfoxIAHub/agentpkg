import json
import math
from typing import List, Dict, Any
from agentpkg.indexers.chunking import chunk_text

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calcula la similitud de cosenos entre dos vectores de igual dimensión."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

class SimpleVectorIndex:
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def add_entry(self, text: str, vector: List[float], metadata: Dict[str, Any] = None):
        self.entries.append({
            "text": text,
            "vector": vector,
            "metadata": metadata or {}
        })

    def build_from_documents(self, documents: List[Dict[str, Any]], connector: Any, chunk_size: int = 500, overlap: int = 50):
        """Procesa documentos, genera fragmentos y calcula sus embeddings para el índice."""
        for doc in documents:
            file_path = doc.get("file_path", "")
            content = doc.get("content", "")
            if isinstance(content, str) and content:
                chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
                if chunks:
                    embeddings = connector.embed(chunks)
                    for chunk, emb in zip(chunks, embeddings):
                        self.add_entry(chunk, emb, metadata={"file_path": file_path, "file": file_path})

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        results = []
        for entry in self.entries:
            sim = cosine_similarity(query_vector, entry["vector"])
            file_path = entry["metadata"].get("file_path", entry["metadata"].get("file", ""))
            results.append({
                "text": entry["text"],
                "score": sim,
                "metadata": entry["metadata"],
                "file_path": file_path
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": self.entries}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimpleVectorIndex":
        index = cls()
        index.entries = data.get("entries", [])
        return index
