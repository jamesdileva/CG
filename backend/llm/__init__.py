"""LLM provider factory"""
from backend.core.config import settings
from .provider import LLMProvider
from .mock import MockLLMProvider
from .ollama import OllamaProvider
import logging

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """Get configured LLM provider"""
    provider_type = settings.llm_provider.lower()

    if provider_type == "mock":
        logger.info("Using mock LLM provider")
        return MockLLMProvider()
    elif provider_type == "ollama":
        logger.info(f"Using Ollama provider at {settings.ollama_base_url}")
        return OllamaProvider()
    else:
        logger.warning(f"Unknown provider {provider_type}, defaulting to mock")
        return MockLLMProvider()


# Global provider instance
_llm_provider = None


async def init_llm():
    """Initialize LLM provider"""
    global _llm_provider
    _llm_provider = get_llm_provider()
    logger.info(f"LLM provider initialized: {type(_llm_provider).__name__}")


def get_llm() -> LLMProvider:
    """Get current LLM provider"""
    if _llm_provider is None:
        raise RuntimeError("LLM provider not initialized. Call init_llm() first.")
    return _llm_provider
