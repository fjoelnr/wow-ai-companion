"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Unified interface for all LLM backends (Ollama, OpenAI, OpenRouter)."""

    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a completion from the given prompt.

        Args:
            prompt: The user prompt / main instruction.
            system: Optional system-level instruction.

        Returns:
            The generated text response.
        """

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the provider is reachable and ready."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'ollama', 'openrouter')."""
