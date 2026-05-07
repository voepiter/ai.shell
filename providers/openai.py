# OpenAI API client
from typing import Dict, List, Optional, Tuple
import requests

from .base import BaseAPIClient


class OpenAIClient(BaseAPIClient):

    API_URL = "https://api.openai.com/v1/chat/completions"

    def _make_request(self, messages: List[Dict], system_instruction: str) -> requests.Response:
        full_messages = []
        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})
        full_messages.extend(messages)

        return requests.post(
            self.API_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": full_messages},
            timeout=self.timeout,
        )

    def extract_response(self, data: Dict) -> str:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Unexpected API response format")

    def extract_usage(self, data: Dict) -> Tuple[Optional[int], Optional[int]]:
        usage = data.get("usage", {})
        return usage.get("prompt_tokens"), usage.get("completion_tokens")

    def _extract_error_message(self, err_data: Dict) -> Optional[str]:
        if "error" in err_data:
            err = err_data["error"]
            if isinstance(err, dict):
                msg = err.get("message", "")
                err_type = err.get("type", "")
                if msg:
                    return f"{err_type}: {msg}" if err_type else msg
        return None

    def list_models(self) -> list:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.json()
        prefixes = ("gpt-", "o1", "o3", "o4")
        return sorted(
            m["id"] for m in data.get("data", [])
            if any(m["id"].startswith(p) for p in prefixes)
        )
