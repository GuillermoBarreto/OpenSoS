import asyncio
import logging
from datetime import datetime, timezone
from time import monotonic

from pydantic import ValidationError

from ..models import Incident
from .models import AIIncidentBrief, GeneratedBrief, IncidentBriefContext, ProviderFact
from .provider import AIProvider

logger = logging.getLogger(__name__)


class IntelligenceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


def build_context(incident: Incident) -> IncidentBriefContext:
    sources = list(dict.fromkeys(source.provider.value for source in incident.sources))
    return IncidentBriefContext(
        incidentId=incident.id, title=incident.title, eventType=incident.type,
        severity=incident.severity, status=incident.status, location=incident.location,
        startedAt=incident.started_at, updatedAt=incident.updated_at, endedAt=incident.ended_at,
        metrics=incident.metrics, sources=sources,
        providerFacts=[ProviderFact(provider=source.provider.value, externalId=source.external_id,
                                    sourceTimestamp=source.updated_at, originalSeverity=source.original_severity)
                       for source in incident.sources],
    )


class IntelligenceService:
    def __init__(self, provider: AIProvider | None, timeout_seconds: float = 20):
        self.provider, self.timeout_seconds = provider, timeout_seconds
        self._cache: dict[tuple[str, str, str], AIIncidentBrief] = {}

    @property
    def available(self) -> bool:
        return self.provider is not None

    async def generate(self, incident: Incident) -> AIIncidentBrief:
        if not self.provider:
            raise IntelligenceError("AI_NOT_CONFIGURED", "AI incident briefs are not configured.")
        context = build_context(incident)
        key = (incident.id, incident.updated_at.isoformat(), self.provider.model)
        cached = self._cache.get(key)
        if cached:
            logger.info("AI brief cache hit incident=%s provider=%s model=%s", incident.id, self.provider.name, self.provider.model)
            return cached.model_copy(update={"cached": True})
        started = monotonic()
        try:
            raw = await asyncio.wait_for(self.provider.generate_incident_brief(context), timeout=self.timeout_seconds)
            generated = GeneratedBrief.model_validate(raw)
        except TimeoutError as exc:
            logger.warning("AI brief timeout incident=%s provider=%s model=%s", incident.id, self.provider.name, self.provider.model)
            raise IntelligenceError("AI_TIMEOUT", "The AI provider timed out. Please retry.", 504) from exc
        except (ValidationError, ValueError, TypeError) as exc:
            logger.warning("AI invalid response incident=%s: %s", incident.id, type(exc).__name__)
            raise IntelligenceError("AI_INVALID_RESPONSE", "The AI provider returned an invalid brief.", 502) from exc
        except Exception as exc:
            logger.exception("AI provider failure incident=%s provider=%s", incident.id, self.provider.name)
            raise IntelligenceError("AI_UNAVAILABLE", "The AI provider is unavailable. Please retry.", 503) from exc
        self._validate_grounding(generated, context)
        brief = AIIncidentBrief(**generated.model_dump(by_alias=True), generatedAt=datetime.now(timezone.utc))
        self._cache[key] = brief
        logger.info("AI brief generated incident=%s provider=%s model=%s duration_ms=%d cache=miss",
                    incident.id, self.provider.name, self.provider.model, (monotonic() - started) * 1000)
        return brief

    @staticmethod
    def _validate_grounding(brief: GeneratedBrief, context: IncidentBriefContext) -> None:
        if not set(brief.sources_used).issubset(context.sources):
            raise IntelligenceError("AI_INVALID_RESPONSE", "The AI provider returned unsupported sources.", 502)
