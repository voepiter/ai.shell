# Base class for API clients
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import sys
import time
import requests
import modules.text as ct


class APIError(Exception):
    pass


class BaseAPIClient(ABC):

    def __init__(self, api_key: str, model: str, timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate_content(self, prompt: str, system_instruction: str = "") -> Tuple[Dict, float]:
        messages = [{"role": "user", "content": prompt}]
        return self._send(messages, system_instruction)

    def generate_chat(self, messages: List[Dict], system_instruction: str = "") -> Tuple[Dict, float]:
        return self._send(messages, system_instruction)

    def _send(self, messages: List[Dict], system_instruction: str) -> Tuple[Dict, float]:
        start_time = time.perf_counter()
        try:
            response = self._make_request(messages, system_instruction)
            response.raise_for_status()
            elapsed = time.perf_counter() - start_time
            # Force utf-8 so response.text uses errors='replace' instead of
            # guess_json_utf which throws UnicodeDecodeError on some responses.
            response.encoding = "utf-8"
            return response.json(), elapsed

        except requests.exceptions.Timeout:
            print(f"\n{ct.forecolor(196)}error: request timeout{ct.resetcolor}", file=sys.stderr)
            raise APIError("request timeout")
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.RequestException:
            print(f"\n{ct.forecolor(196)}error: network connection error{ct.resetcolor}", file=sys.stderr)
            raise APIError("network connection error")

    @abstractmethod
    def _make_request(self, messages: List[Dict], system_instruction: str) -> requests.Response:
        # messages = [{"role": "user"|"assistant", "content": "..."}]
        pass

    def _handle_http_error(self, e: requests.exceptions.HTTPError):
        msg = str(e).split(" for url: https:")[0]
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                err_data = resp.json()
            except ValueError:
                err_data = None
            if isinstance(err_data, dict):
                detail_msg = self._extract_error_message(err_data)
                if detail_msg:
                    msg = detail_msg
        print(f"\n{ct.forecolor(219)}error: {msg}{ct.resetcolor}", file=sys.stderr)
        raise APIError(msg)

    def _extract_error_message(self, err_data: Dict) -> Optional[str]:
        if "error" not in err_data:
            return None
        err = err_data["error"]
        if not isinstance(err, dict):
            return None
        parts = []
        code = err.get("code")
        status = err.get("status")
        detail = err.get("message")
        if code is not None:
            parts.append(str(code))
        if status:
            parts.append(status)
        if detail:
            parts.append(detail)
        return " ".join(parts) if parts else None

    def list_models(self) -> list:
        raise NotImplementedError(f"list_models not supported for {self.__class__.__name__}")

    @abstractmethod
    def extract_response(self, data: Dict) -> str:
        pass

    @abstractmethod
    def extract_usage(self, data: Dict) -> Tuple[Optional[int], Optional[int]]:
        pass
