from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class IncidentType(StrEnum):
    EARTHQUAKE = "EARTHQUAKE"
    WILDFIRE = "WILDFIRE"
    TROPICAL_CYCLONE = "TROPICAL_CYCLONE"
    FLOOD = "FLOOD"
    VOLCANO = "VOLCANO"
    SEVERE_WEATHER = "SEVERE_WEATHER"
    TSUNAMI = "TSUNAMI"
    DROUGHT = "DROUGHT"
    OTHER = "OTHER"


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    UNKNOWN = "UNKNOWN"


class ProviderName(StrEnum):
    USGS = "USGS"
    EONET = "NASA EONET"
    GDACS = "GDACS"


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country: str | None = None
    region: str | None = None
    place_name: str | None = Field(None, alias="placeName")

    model_config = {"populate_by_name": True}


class IncidentSource(BaseModel):
    provider: ProviderName
    external_id: str = Field(alias="externalId")
    url: HttpUrl
    updated_at: datetime = Field(alias="updatedAt")
    original_severity: str | None = Field(None, alias="originalSeverity")

    model_config = {"populate_by_name": True}


class Incident(BaseModel):
    id: str
    external_ids: list[str] = Field(alias="externalIds")
    type: IncidentType
    title: str
    description: str | None = None
    severity: Severity
    status: IncidentStatus
    location: Location
    geometry: dict[str, Any] | None = None
    started_at: datetime = Field(alias="startedAt")
    updated_at: datetime = Field(alias="updatedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    sources: list[IncidentSource]
    metrics: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")

    model_config = {"populate_by_name": True}


class ProviderStatus(BaseModel):
    provider: ProviderName
    status: Literal["LIVE", "DEGRADED", "SYNCING"]
    last_successful_sync: datetime | None = Field(None, alias="lastSuccessfulSync")
    last_attempt: datetime | None = Field(None, alias="lastAttempt")
    last_error: str | None = Field(None, alias="lastError")
    data_age_seconds: int | None = Field(None, alias="dataAgeSeconds")
    incident_count: int = Field(0, alias="incidentCount")

    model_config = {"populate_by_name": True}


class IncidentCollection(BaseModel):
    incidents: list[Incident]
    total: int
    generated_at: datetime = Field(alias="generatedAt")
    providers: list[ProviderStatus]

    model_config = {"populate_by_name": True}

