"""Anthropic Claude API client (api.anthropic.com/v1/messages)."""
from typing import Dict, List, Optional, Tuple
import requests

from .base import BaseAPIClient


class AnthropicClient(BaseAPIClient):

    _HEADERS = {"anthropic-version": "2023-06-01"}

    def _make_request(self, messages: List[Dict], system_instruction: str) -> requests.Response:
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system_instruction:
            payload["system"] = system_instruction

        return requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={**self._HEADERS, "x-api-key": self.api_key},
            json=payload,
            timeout=self.timeout,
        )

    def extract_response(self, data: Dict) -> str:
        try:
            content = data["content"]
            if isinstance(content, list) and content:
                return content[0].get("text", "")
            raise ValueError("Unexpected API response format")
        except (KeyError, IndexError, TypeError):
            raise ValueError("Unexpected API response format")

    def extract_usage(self, data: Dict) -> Tuple[Optional[int], Optional[int]]:
        usage = data.get("usage", {})
        return usage.get("input_tokens"), usage.get("output_tokens")

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
            "https://api.anthropic.com/v1/models",
            headers={**self._HEADERS, "x-api-key": self.api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.json()
        return [m["id"] for m in data.get("data", [])]
