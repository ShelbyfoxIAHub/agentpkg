import json
import urllib.request
import urllib.error
from typing import List, Dict, Any
from agentpkg.connectors.base import ModelConnector

class OllamaConnector(ModelConnector):
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434", timeout: int = 60, batch_size: int = 32):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.batch_size = batch_size

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.host}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": False}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("message", {}).get("content", "")

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        if not texts:
            return []
        
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            url = f"{self.host}/api/embed"
            payload = {"model": self.model, "input": batch}
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    all_embeddings.extend(res.get("embeddings", []))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    all_embeddings.extend(self._embed_legacy(batch))
                else:
                    raise e
                    
        return all_embeddings

    def _embed_legacy(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        url = f"{self.host}/api/embeddings"
        for text in texts:
            payload = {"model": self.model, "prompt": text}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res = json.loads(response.read().decode("utf-8"))
                embeddings.append(res.get("embedding", []))
        return embeddings
