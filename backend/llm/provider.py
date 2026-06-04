"""LLM provider abstraction layer"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def chat(self, messages: list[dict]) -> str:
        """Chat interface"""
        pass
