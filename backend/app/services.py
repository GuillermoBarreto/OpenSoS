import asyncio
import math
from datetime import datetime, timezone

from .models import Incident, ProviderName, ProviderStatus
from .providers import Provider


class IncidentRepository:
    def __init__(self):
        self._by_provider: dict[ProviderName, list[Incident]] = {}

    def replace_provider(self, provider: ProviderName, incidents: list[Incident]) -> None:
        self._by_provider[provider] = incidents

    def all(self) -> list[Incident]:
        return deduplicate([item for items in self._by_provider.values() for item in items])


def distance_km(a: Incident, b: Incident) -> float:
    lat1, lat2 = math.radians(a.location.latitude), math.radians(b.location.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.location.longitude - a.location.longitude)
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(value))


def deduplicate(incidents: list[Incident]) -> list[Incident]:
    """Only merge cross-provider earthquakes within 30 km and 10 minutes."""
    result: list[Incident] = []
    for incident in sorted(incidents, key=lambda item: item.updated_at, reverse=True):
        match = next((item for item in result if item.type == incident.type and item.type.value == "EARTHQUAKE"
                      and not {s.provider for s in item.sources}.intersection(s.provider for s in incident.sources)
                      and abs((item.started_at - incident.started_at).total_seconds()) <= 600
                      and distance_km(item, incident) <= 30), None)
        if match:
            match.external_ids = list(dict.fromkeys(match.external_ids + incident.external_ids))
            match.sources.extend(source for source in incident.sources if source.external_id not in {s.external_id for s in match.sources})
            match.updated_at = max(match.updated_at, incident.updated_at)
            match.provenance["deduplicated"] = True
        else: result.append(incident.model_copy(deep=True))
    return result


class SyncService:
    def __init__(self, providers: list[Provider], repository: IncidentRepository):
        self.providers, self.repository = providers, repository
        self.statuses = {p.name: ProviderStatus(provider=p.name, status="SYNCING") for p in providers}
        self._lock = asyncio.Lock()

    async def sync_all(self) -> None:
        async with self._lock:
            await asyncio.gather(*(self._sync(provider) for provider in self.providers))

    async def sync_provider(self, provider: Provider) -> None:
        async with self._lock:
            await self._sync(provider)

    async def _sync(self, provider: Provider) -> None:
        now = datetime.now(timezone.utc)
        status = self.statuses[provider.name]
        status.last_attempt = now
        try:
            incidents = await provider.fetch()
            self.repository.replace_provider(provider.name, incidents)
            status.status, status.last_successful_sync, status.last_error = "LIVE", now, None
            status.incident_count = len(incidents)
        except Exception as exc:
            status.status, status.last_error = "DEGRADED", str(exc)[:240]
        self.refresh_ages()

    def refresh_ages(self) -> None:
        now = datetime.now(timezone.utc)
        for status in self.statuses.values():
            status.data_age_seconds = int((now - status.last_successful_sync).total_seconds()) if status.last_successful_sync else None
