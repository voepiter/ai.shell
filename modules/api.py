"""Factory for creating API provider clients."""
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


# Maps provider names to client classes and their API key env vars
class APIFactory:
    # Provider name → client class
    PROVIDERS = {
        "google":     GoogleClient,
        "openai":     OpenAIClient,
        "xai":        XAIClient,
        "deepseek":   DeepSeekClient,
        "anthropic":  AnthropicClient,
        "openrouter": OpenRouterClient,
    }

    # Provider name → expected API key environment variable
    API_KEY_ENV_VARS = {
        "google":     "GEMINI_API_KEY",
        "openai":     "OPENAI_API_KEY",
        "xai":        "XAI_API_KEY",
        "deepseek":   "DEEPSEEK_API_KEY",
        "anthropic":  "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    @classmethod
    def create_client(
        cls,
        provider:      Optional[str] = None,
        api_key:       Optional[str] = None,
        model:         Optional[str] = None,
        timeout:       int = 30,
        config_loader=None,
    ) -> BaseAPIClient:
        """Instantiate the right provider client; resolves api_key from env or ai.ini."""
        provider = (provider or os.getenv("AI_PROVIDER", "google")).lower()
        if provider not in cls.PROVIDERS:
            supported = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider: '{provider}'. Supported: {supported}")

        # Resolve API key: argument → env var → ai.ini [api_keys]
        if not api_key:
            env_var = cls.API_KEY_ENV_VARS[provider]
            api_key = os.getenv(env_var)
            if not api_key and config_loader is not None:
                api_key = config_loader.get_api_key(env_var)
            if not api_key:
                raise ValueError(f"{env_var} is not set (env var or [api_keys] in ai.ini)")

        if not model:
            raise ValueError(
                f"No model configured for '{provider}'. "
                f"Set it in ai.ini under [models] {provider} = <model-name>"
            )
        return cls.PROVIDERS[provider](api_key=api_key, model=model, timeout=timeout)

    # Return list of supported provider names
    @classmethod
    def list_providers(cls) -> list:
        return list(cls.PROVIDERS.keys())
