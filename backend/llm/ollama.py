"""Ollama LLM provider for local model inference using the chat API with system persona."""
import json
import logging

import httpx
from pydantic import BaseModel

from backend.core.config import settings
from backend.llm.provider import GenerationParams, LLMProvider
from backend.llm.retry import async_retry

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a writer/researcher for a documentary studio that produces YouTube videos about wild, bizarre, and little-known history. Your tone is engaging, conversational, and occasionally dramatic — think History Channel documentary narrator energy. You always maintain factual accuracy and only reference real, verifiable events and sources.

RULES:
- Always respond in the exact format requested (JSON when asked, script format when asked)
- Never invent facts, dates, or events
- If you're uncertain about a detail, omit it rather than guess
- Keep responses substantive and detailed — 10-18 minute documentary content
- Use natural, engaging language — not academic, not overly casual"""


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference using httpx."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.client = httpx.AsyncClient(timeout=settings.ollama_timeout_seconds)

    def _chat_payload(self, prompt: str, params: GenerationParams | None, format_json: bool = False) -> dict:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        options: dict = {}
        if params:
            if params.temperature != 0.7:
                options["temperature"] = params.temperature
            if params.max_tokens != 2048:
                options["num_predict"] = params.max_tokens
            if params.top_p != 0.9:
                options["top_p"] = params.top_p
            if params.top_k != 40:
                options["top_k"] = params.top_k
            if params.stop:
                payload["stop"] = params.stop
            if params.frequency_penalty != 0.0:
                options["frequency_penalty"] = params.frequency_penalty
            if params.presence_penalty != 0.0:
                options["presence_penalty"] = params.presence_penalty
            if params.seed is not None:
                options["seed"] = params.seed
            if params.num_ctx is not None:
                options["num_ctx"] = params.num_ctx
        if options:
            payload["options"] = options
        if format_json:
            payload["format"] = "json"
        return payload

    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(httpx.HTTPError,))
    async def generate(self, prompt: str, params: GenerationParams | None = None) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=self._chat_payload(prompt, params),
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(httpx.HTTPError,))
    async def chat(self, messages: list[dict], params: GenerationParams | None = None) -> str:
        full_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
        payload: dict = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
        }
        if params:
            if params.temperature != 0.7:
                payload["temperature"] = params.temperature
            if params.max_tokens != 2048:
                payload["max_tokens"] = params.max_tokens
            if params.top_p != 0.9:
                payload["top_p"] = params.top_p
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(httpx.HTTPError, json.JSONDecodeError, ValueError))
    async def generate_structured(
        self,
        prompt: str,
        params: GenerationParams | None = None,
        schema: type[BaseModel] | None = None,
    ) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=self._chat_payload(prompt, params, format_json=True),
        )
        response.raise_for_status()
        raw = response.json()["message"]["content"]
        data = json.loads(raw)
        if schema:
            data = schema(**data).model_dump()
        return data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
