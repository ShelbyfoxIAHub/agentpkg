"""Simple JSON-based vector index generator and retriever for agentpkg."""

import math
from typing import List, Dict, Any
from agentpkg.indexers.chunker import chunk_text
from agentpkg.connectors.base import BaseConnector


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two numerical vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class SimpleVectorIndex:
    """In-memory and JSON-serializable vector index for portability."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def build_from_documents(
        self, documents: List[Dict[str, str]], connector: BaseConnector, chunk_size: int = 500
    ) -> None:
        """
        Processes list of documents [{"file_path": "...", "content": "..."}],
        chunks text, generates embeddings via connector, and populates index.
        """
        all_chunks = []
        metadata_map = []

        for doc in documents:
            file_path = doc.get("file_path", "unknown")
            text = doc.get("content", "")
            doc_chunks = chunk_text(text, chunk_size=chunk_size)

            for chunk in doc_chunks:
                all_chunks.append(chunk["text"])
                metadata_map.append({
                    "file_path": file_path,
                    "text": chunk["text"],
                    "start": chunk["start"],
                    "end": chunk["end"],
                })

        if not all_chunks:
            return

        embeddings = connector.embed(all_chunks)

        for meta, vector in zip(metadata_map, embeddings):
            self.entries.append({
                "file_path": meta["file_path"],
                "text": meta["text"],
                "start": meta["start"],
                "end": meta["end"],
                "vector": vector,
            })

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches top_k most similar entries given a query embedding vector."""
        results = []
        for entry in self.entries:
            sim = cosine_similarity(query_vector, entry["vector"])
            results.append({
                "file_path": entry["file_path"],
                "text": entry["text"],
                "score": sim,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes index data into a standard dictionary structure."""
        return {"version": "1.0", "count": len(self.entries), "entries": self.entries}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimpleVectorIndex":
        """Reconstructs index instance from dictionary data."""
        index = cls()
        index.entries = data.get("entries", [])
        return index
