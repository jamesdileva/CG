"""Mock LLM provider for testing without API calls"""
from .provider import LLMProvider
import logging
import json

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Mock provider that returns synthetic data for testing"""

    MOCK_TOPICS = [
        "The Great Molasses Flood of 1919",
        "How the Printing Press Changed History",
        "The Mystery of the Voynich Manuscript",
        "The Lost City of Atlantis: Myths vs Facts",
        "How Penicillin Was Discovered by Accident",
    ]

    MOCK_SCRIPTS = {
        "The Great Molasses Flood of 1919": """On January 15, 1919, in Boston, Massachusetts, one of the most unusual disasters
struck the city. A massive tank containing 2.3 million gallons of molasses ruptured and created a tidal wave of molasses
that swept through the streets. This documentary explores the engineering failure, the lives lost, and the aftermath
of this tragic and bizarre event.""",
        "How the Printing Press Changed History": """Before Gutenberg's printing press, all books had to be copied by hand.
This revolutionary invention in 1440 transformed human knowledge and culture. We explore how the printing press led to
the Renaissance, the Reformation, and the Age of Enlightenment.""",
    }

    async def generate(self, prompt: str) -> str:
        """Return mock response based on prompt type"""
        logger.info(f"Mock LLM: {prompt[:50]}...")

        if "topic" in prompt.lower() or "generate" in prompt.lower():
            return json.dumps([{"title": topic} for topic in self.MOCK_TOPICS[:5]])

        return "Mock response generated successfully."

    async def chat(self, messages: list[dict]) -> str:
        """Chat with mock provider"""
        logger.info(f"Mock chat: {len(messages)} messages")

        last_message = messages[-1]["content"] if messages else ""

        if "script" in last_message.lower():
            return self.MOCK_SCRIPTS.get(
                "The Great Molasses Flood of 1919",
                "Mock script generated successfully."
            )

        if "topic" in last_message.lower():
            return json.dumps(self.MOCK_TOPICS[:3])

        return "Mock response from chat."
