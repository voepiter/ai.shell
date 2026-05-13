"""Google Gemini API client (generativelanguage.googleapis.com)."""
from typing import Dict, List, Optional, Tuple
import requests

from .base import BaseAPIClient


class GoogleClient(BaseAPIClient):

    def _make_request(self, messages: List[Dict], system_instruction: str) -> requests.Response:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.model}:generateContent"
        )

        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else m["role"]
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload: dict = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        return requests.post(
            url,
            params={"key": self.api_key},
            json=payload,
            timeout=self.timeout,
        )

    def list_models(self) -> list:
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        response = requests.get(url, params={"key": self.api_key}, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.json()
        models = []
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                name = m["name"]
                if name.startswith("models/"):
                    name = name[len("models/"):]
                models.append(name)
        return sorted(models)

    def extract_response(self, data: Dict) -> str:
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Unexpected API response format")

    def extract_usage(self, data: Dict) -> Tuple[Optional[int], Optional[int]]:
        usage = data.get("usageMetadata", {})
        return usage.get("promptTokenCount"), usage.get("candidatesTokenCount")
