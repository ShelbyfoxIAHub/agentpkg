"""OpenAI-compatible model connector using Python standard library."""

import json
import os
import urllib.request
from typing import List, Dict, Any
from agentpkg.connectors.base import BaseConnector


class OpenAIConnector(BaseConnector):
    """Connector for OpenAI-compatible APIs (vLLM, LM Studio, OpenAI, etc.)."""

    def __init__(self, model: str = "gpt-4o", api_key: str = None, base_url: str = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
        }
        payload.update(kwargs)

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._get_headers(),
            method="POST",
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            choices = res_data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
        }
        payload.update(kwargs)

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._get_headers(),
            method="POST",
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            data = res_data.get("data", [])
            return [item.get("embedding", []) for item in data]
