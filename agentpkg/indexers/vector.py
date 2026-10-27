import math
import json
from typing import List, Dict, Any, Tuple

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calcula la similitud coseno entre dos vectores de igual dimension."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)

class VectorIndex:
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def add_entry(self, chunk_text: str, source_file: str, embedding: List[float]):
        """Añade un fragmento con su vector e identificador de origen."""
        self.entries.append({
            "text": chunk_text,
            "source": source_file,
            "vector": embedding
        })

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        """Busca los fragmentos mas similares al vector de consulta."""
        results = []
        for entry in self.entries:
            sim = cosine_similarity(query_vector, entry["vector"])
            results.append((sim, entry))
            
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def to_json(self) -> str:
        """Serializa el indice a JSON para guardarlo en index/ dentro del paquete."""
        return json.dumps(self.entries, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "VectorIndex":
        """Carga un indice vectorial desde un string JSON."""
        idx = cls()
        idx.entries = json.loads(json_str)
        return idx
