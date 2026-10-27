import os
import json
import urllib.request
from typing import List, Dict, Any
from agentpkg.connectors.base import ModelConnector

class OpenAIConnector(ModelConnector):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = None, base_url: str = "https://api.openai.com/v1"):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model, "messages": messages}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"]

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        url = f"{self.base_url}/embeddings"
        payload = {"model": "text-embedding-3-small", "input": texts}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            return [item["embedding"] for item in res.get("data", [])]
