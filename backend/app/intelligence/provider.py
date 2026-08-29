import json
from abc import ABC, abstractmethod

from .models import GeneratedBrief, IncidentBriefContext
from .prompts import SYSTEM_PROMPT


class AIProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def generate_incident_brief(self, context: IncidentBriefContext) -> GeneratedBrief: ...


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout_seconds: float):
        from openai import AsyncOpenAI

        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)

    async def generate_incident_brief(self, context: IncidentBriefContext) -> GeneratedBrief:
        schema = GeneratedBrief.model_json_schema(by_alias=True)
        response = await self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input="<incident_context>\n" + context.model_dump_json(by_alias=True) + "\n</incident_context>",
            temperature=0,
            text={"format": {"type": "json_schema", "name": "incident_brief", "strict": True, "schema": schema}},
        )
        return GeneratedBrief.model_validate(json.loads(response.output_text))
