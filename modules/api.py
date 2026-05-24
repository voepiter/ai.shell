"""Factory for creating API provider clients."""
import os
from providers import (
    BaseAPIClient,
    GoogleClient,
    OpenAIClient,
    XAIClient,
    DeepSeekClient,
    AnthropicClient,
    OpenRouterClient,
)
from .config import ConfigLoader


# Maps provider name → (client class, API key env var)
class APIFactory:
    PROVIDERS: dict[str, tuple] = {
        "google":     (GoogleClient,     "GEMINI_API_KEY"),
        "openai":     (OpenAIClient,     "OPENAI_API_KEY"),
        "xai":        (XAIClient,        "XAI_API_KEY"),
        "deepseek":   (DeepSeekClient,   "DEEPSEEK_API_KEY"),
        "anthropic":  (AnthropicClient,  "ANTHROPIC_API_KEY"),
        "openrouter": (OpenRouterClient, "OPENROUTER_API_KEY"),
    }

    # Instantiate the right provider client; resolves api_key from env or ai.ini
    @classmethod
    def create_client(
        cls,
        provider:      str | None = None,
        api_key:       str | None = None,
        model:         str | None = None,
        timeout:       int = 30,
        config_loader: ConfigLoader | None = None,
    ) -> BaseAPIClient:
        provider = (provider or os.getenv("AI_PROVIDER", "google")).lower()
        if provider not in cls.PROVIDERS:
            supported = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider: '{provider}'. Supported: {supported}")

        client_cls, env_var = cls.PROVIDERS[provider]

        # Resolve API key: argument → env var → ai.ini [api_keys]
        if not api_key:
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
        return client_cls(api_key=api_key, model=model, timeout=timeout)

    # Return list of supported provider names
    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls.PROVIDERS.keys())
