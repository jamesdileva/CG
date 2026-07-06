"""LLM provider abstraction layer"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import logging

from pydantic import BaseModel

from backend.llm.retry import async_retry

logger = logging.getLogger(__name__)


@dataclass
class GenerationParams:
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40
    stop: list[str] | None = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    seed: int | None = None
    num_ctx: int | None = None


class LLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def generate(self, prompt: str, params: GenerationParams | None = None) -> str:
        """Generate text from a prompt"""
        pass

    @abstractmethod
    async def chat(self, messages: list[dict], params: GenerationParams | None = None) -> str:
        """Chat interface"""
        pass

    async def generate_structured(
        self,
        prompt: str,
        params: GenerationParams | None = None,
        schema: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON output.

        Prompts the model to return JSON, parses it, and optionally
        validates against a pydantic schema. Retries on parse/validate failure.
        """
        # Subclasses can override, but this provides a default fallback
        raw = await self.generate(prompt, params)

        for attempt in range(3):
            try:
                import json
                data = json.loads(raw)
                if schema:
                    data = schema(**data).model_dump()
                return data
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                logger.warning("Structured parse failed (attempt %d/3): %s", attempt + 1, exc)
                if attempt < 2:
                    raw = await self.generate(prompt, params)
                else:
                    raise ValueError(f"Failed to parse structured output after 3 attempts: {exc}") from exc

        raise RuntimeError("Unreachable")
