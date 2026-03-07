"""Ollama (local) LLM provider."""

import logging

import httpx

from .base import LLMProvider

log = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Calls a local Ollama instance for text generation."""

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "llama3.2",
        fallback_model: str | None = "mistral-nemo",
        timeout: float = 120,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._fallback = fallback_model
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/api/generate", json=payload
                )
                if resp.is_success:
                    return resp.json().get("response", "")
            except httpx.HTTPError as exc:
                log.warning("Ollama primary model failed: %s", exc)

            # Fallback model
            if self._fallback:
                log.info("Trying fallback model: %s", self._fallback)
                payload["model"] = self._fallback
                resp = await client.post(
                    f"{self._base_url}/api/generate", json=payload
                )
                resp.raise_for_status()
                return resp.json().get("response", "")

        return ""

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.is_success
        except httpx.HTTPError:
            return False
