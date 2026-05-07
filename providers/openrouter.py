# OpenRouter API client — unified gateway to multiple LLM providers
from typing import Dict, List, Optional, Tuple
import requests

from .openai import OpenAIClient


class OpenRouterClient(OpenAIClient):

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

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

    def list_models(self) -> list:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.json()

        result = []
        for m in data.get("data", []):
            mid = m.get("id", "")
            if not mid:
                continue
            pricing = m.get("pricing", {})
            try:
                price_per_m = float(pricing.get("prompt", 0)) * 1_000_000
                price_str = "free" if price_per_m == 0 else f"${price_per_m:.3f}/1M"
            except (TypeError, ValueError):
                price_str = ""
            result.append((mid, price_str))

        result.sort(key=lambda x: x[0])
        return result

    def _extract_error_message(self, err_data: Dict) -> Optional[str]:
        if "error" in err_data:
            err = err_data["error"]
            if isinstance(err, dict):
                msg = err.get("message", "")
                code = err.get("code", "")
                if msg:
                    return f"{code}: {msg}" if code else msg
        return None
