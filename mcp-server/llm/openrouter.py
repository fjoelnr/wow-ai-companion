"""OpenRouter LLM provider (OpenAI-compatible API with model routing)."""

import logging

import httpx

from .base import LLMProvider

log = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    """Calls the OpenRouter API for access to many models via one key.

    OpenRouter uses the OpenAI chat/completions format.
    See https://openrouter.ai/docs for model list and pricing.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-sonnet-4",
        base_url: str = OPENROUTER_BASE,
        timeout: float = 90,
        temperature: float = 0.2,
        app_name: str = "WoW AI Companion",
        app_url: str = "https://github.com/fjoelnr/wow-ai-companion",
    ):
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._temperature = temperature
        self._app_name = app_name
        self._app_url = app_url

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._app_url,
            "X-Title": self._app_name,
        }
        body = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            # OpenRouter returns usage info + model used
            if "choices" in data and data["choices"]:
                model_used = data.get("model", self._model)
                log.info("OpenRouter used model: %s", model_used)
                return data["choices"][0]["message"]["content"]

            log.warning("OpenRouter returned unexpected response: %s", data)
            return ""

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self._base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                return resp.is_success
        except httpx.HTTPError:
            return False
