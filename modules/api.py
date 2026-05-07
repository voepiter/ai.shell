# Factory for creating API provider clients
import os
from typing import Optional

from providers import (
    BaseAPIClient,
    GoogleClient,
    OpenAIClient,
    XAIClient,
    DeepSeekClient,
    AnthropicClient,
    OpenRouterClient,
)


class APIFactory:
    PROVIDERS = {
        "google":     GoogleClient,
        "openai":     OpenAIClient,
        "xai":        XAIClient,
        "deepseek":   DeepSeekClient,
        "anthropic":  AnthropicClient,
        "openrouter": OpenRouterClient,
    }

    API_KEY_ENV_VARS = {
        "google":     "GOOGLE_API_KEY",
        "openai":     "OPENAI_API_KEY",
        "xai":        "XAI_API_KEY",
        "deepseek":   "DEEPSEEK_API_KEY",
        "anthropic":  "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    @classmethod
    def create_client(
        cls,
        provider:  Optional[str] = None,
        api_key:   Optional[str] = None,
        model:     Optional[str] = None,
        timeout:   int = 30,
    ) -> BaseAPIClient:
        provider = (provider or os.getenv("AI_PROVIDER", "google")).lower()
        if provider not in cls.PROVIDERS:
            supported = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider: '{provider}'. Supported: {supported}")
        if not api_key:
            env_var = cls.API_KEY_ENV_VARS[provider]
            api_key = os.getenv(env_var)
            if not api_key:
                raise ValueError(f"{env_var} environment variable is not set")
        if not model:
            raise ValueError(
                f"No model configured for '{provider}'. "
                f"Set it in ai.ini under [models] {provider} = <model-name>"
            )
        return cls.PROVIDERS[provider](api_key=api_key, model=model, timeout=timeout)

    @classmethod
    def list_providers(cls) -> list:
        return list(cls.PROVIDERS.keys())
