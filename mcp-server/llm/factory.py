"""Factory for creating LLM provider instances from environment config."""

import logging
import os

from .base import LLMProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider

log = logging.getLogger(__name__)

# ── Environment variable names ──────────────────────────────────────────
_ENV_PROVIDER = "LLM_PROVIDER"  # ollama | openai | openrouter
# Backward compat: LLM_MODE is the old name
_ENV_MODE = "LLM_MODE"

# Ollama
_ENV_OLLAMA_BASE = "OLLAMA_BASE_URL"
_ENV_OLLAMA_MODEL = "OLLAMA_MODEL"
_ENV_OLLAMA_FALLBACK = "OLLAMA_FALLBACK_MODEL"

# OpenAI
_ENV_OPENAI_KEY = "OPENAI_API_KEY"
_ENV_OPENAI_MODEL = "OPENAI_MODEL"

# OpenRouter
_ENV_OPENROUTER_KEY = "OPENROUTER_API_KEY"
_ENV_OPENROUTER_MODEL = "OPENROUTER_MODEL"


def _resolve_provider_name() -> str:
    """Determine provider name from env, with backward compatibility."""
    name = os.getenv(_ENV_PROVIDER, "").strip().lower()
    if name:
        return name

    # Backward compat: LLM_MODE=api → openai, LLM_MODE=local → ollama
    mode = os.getenv(_ENV_MODE, "local").strip().lower()
    if mode == "api":
        return "openai"
    return "ollama"


def get_provider(name: str | None = None) -> LLMProvider:
    """Create and return an LLM provider based on name or environment.

    Args:
        name: Provider name override. If None, reads from environment.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If the provider name is unknown or required keys are missing.
    """
    provider_name = (name or _resolve_provider_name()).strip().lower()

    if provider_name == "ollama":
        provider = OllamaProvider(
            base_url=os.getenv(_ENV_OLLAMA_BASE, "http://ollama:11434"),
            model=os.getenv(_ENV_OLLAMA_MODEL, "llama3.2"),
            fallback_model=os.getenv(_ENV_OLLAMA_FALLBACK, "mistral-nemo") or None,
        )
    elif provider_name == "openai":
        api_key = os.getenv(_ENV_OPENAI_KEY, "")
        if not api_key:
            raise ValueError(
                f"LLM_PROVIDER=openai requires {_ENV_OPENAI_KEY} to be set"
            )
        provider = OpenAIProvider(
            api_key=api_key,
            model=os.getenv(_ENV_OPENAI_MODEL, "gpt-4o-mini"),
        )
    elif provider_name == "openrouter":
        api_key = os.getenv(_ENV_OPENROUTER_KEY, "")
        if not api_key:
            raise ValueError(
                f"LLM_PROVIDER=openrouter requires {_ENV_OPENROUTER_KEY} to be set"
            )
        provider = OpenRouterProvider(
            api_key=api_key,
            model=os.getenv(_ENV_OPENROUTER_MODEL, "anthropic/claude-sonnet-4"),
        )
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider_name}'. "
            "Supported: ollama, openai, openrouter"
        )

    log.info("LLM provider initialized: %s (%s)", provider.name, type(provider).__name__)
    return provider
