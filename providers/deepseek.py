"""DeepSeek API client (api.deepseek.com/v1/chat/completions)."""
import requests

from .openai import OpenAIClient


class DeepSeekClient(OpenAIClient):

    API_URL = "https://api.deepseek.com/v1/chat/completions"

    def list_models(self) -> list:
        response = requests.get(
            "https://api.deepseek.com/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.json()
        return sorted(m["id"] for m in data.get("data", []))
