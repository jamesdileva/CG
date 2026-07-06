"""Mock LLM provider for testing without API calls"""
import json
import logging

from pydantic import BaseModel

from backend.llm.provider import GenerationParams, LLMProvider

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
        "The Great Molasses Flood of 1919": """[NARRATOR:] On January 15, 1919, in Boston, Massachusetts, one of the most unusual disasters struck the city.

[SECTION: The Disaster]

[NARRATOR:] A massive tank containing 2.3 million gallons of molasses ruptured and created a tidal wave of molasses that swept through the streets at 35 miles per hour.
[VISUAL: archival photo of the wreckage]

This documentary explores the engineering failure, the lives lost, and the aftermath of this tragic and bizarre event.""",
        "How the Printing Press Changed History": """[NARRATOR:] Before Gutenberg's printing press, all books had to be copied by hand.

[SECTION: The Invention]

[NARRATOR:] This revolutionary invention in 1440 transformed human knowledge and culture. We explore how the printing press led to the Renaissance, the Reformation, and the Age of Enlightenment.
[VISUAL: illustration of Gutenberg press]""",
    }

    async def generate(self, prompt: str, params: GenerationParams | None = None) -> str:
        """Return mock response based on prompt type"""
        logger.info(f"Mock LLM generate: {prompt[:60]}...")

        if "topic" in prompt.lower() or "generate" in prompt.lower():
            topics = [{"title": topic, "description": f"A documentary about {topic}."} for topic in self.MOCK_TOPICS[:5]]
            return json.dumps({"topics": topics})

        return "Mock response generated successfully."

    async def chat(self, messages: list[dict], params: GenerationParams | None = None) -> str:
        """Chat with mock provider"""
        logger.info(f"Mock chat: {len(messages)} messages")

        last_message = messages[-1]["content"] if messages else ""

        if "script" in last_message.lower():
            return self.MOCK_SCRIPTS.get(
                "The Great Molasses Flood of 1919",
                "Mock script generated successfully.",
            )

        if "topic" in last_message.lower():
            return json.dumps(self.MOCK_TOPICS[:3])

        return "Mock response from chat."

    async def generate_structured(
        self,
        prompt: str,
        params: GenerationParams | None = None,
        schema: type[BaseModel] | None = None,
    ) -> dict:
        raw = await self.generate(prompt, params)
        data = json.loads(raw)
        if schema:
            data = schema(**data).model_dump()
        return data
