"""Ollama LLM provider for local model inference"""
from .provider import LLMProvider
import httpx
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference"""

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate(self, prompt: str) -> str:
        """Generate text using Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.HTTPError as e:
            logger.error(f"Ollama error: {e}")
            raise

    async def chat(self, messages: list[dict]) -> str:
        """Chat with Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
