from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..datetime_utils import ensure_utc
from ..models import IncidentStatus, IncidentType, Location, Severity


class ProviderFact(BaseModel):
    provider: str
    external_id: str = Field(alias="externalId")
    source_timestamp: datetime = Field(alias="sourceTimestamp")
    original_severity: str | None = Field(None, alias="originalSeverity")

    @field_validator("source_timestamp")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    model_config = {"populate_by_name": True}


class IncidentBriefContext(BaseModel):
    incident_id: str = Field(alias="incidentId")
    title: str
    event_type: IncidentType = Field(alias="eventType")
    severity: Severity
    status: IncidentStatus
    location: Location
    started_at: datetime = Field(alias="startedAt")
    updated_at: datetime = Field(alias="updatedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    metrics: dict[str, str | int | float | bool | None]
    provider_facts: list[ProviderFact] = Field(alias="providerFacts")
    sources: list[str]

    model_config = {"populate_by_name": True}


class GeneratedBrief(BaseModel):
    headline: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=1200)
    key_points: list[str] = Field(alias="keyPoints", max_length=5)
    sources_used: list[str] = Field(alias="sourcesUsed", min_length=1)

    @field_validator("key_points")
    @classmethod
    def concise_points(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 240 for value in values):
            raise ValueError("key points must be non-empty and at most 240 characters")
        return values

    model_config = {"populate_by_name": True}


class AIIncidentBrief(GeneratedBrief):
    generated_at: datetime = Field(alias="generatedAt")
    cached: bool = False

    @field_validator("generated_at")
    @classmethod
    def generated_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
