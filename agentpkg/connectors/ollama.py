"""Ollama model connector using Python standard library."""

import json
import os
import urllib.error
import urllib.request
from typing import List, Dict, Any
from agentpkg.connectors.base import BaseConnector


class OllamaConnector(BaseConnector):
    """Connector for local Ollama instance (http://localhost:11434 by default)."""

    def __init__(self, model: str = "llama3", host: str = None):
        self.model = model
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        payload.update(kwargs)

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("message", {}).get("content", "")

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        # Intentar con la API moderna de Ollama (/api/embed)
        url_embed = f"{self.host}/api/embed"
        payload = {"model": self.model, "input": texts}
        payload.update(kwargs)

        req = urllib.request.Request(
            url_embed,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if "embeddings" in res_data:
                    return res_data["embeddings"]
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise

        # Respaldo para versiones legacy de Ollama (/api/embeddings)
        embeddings = []
        for text in texts:
            url = f"{self.host}/api/embeddings"
            payload = {"model": self.model, "prompt": text}
            payload.update(kwargs)

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                embeddings.append(res_data.get("embedding", []))

        return embeddings
