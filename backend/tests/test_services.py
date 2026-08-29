from datetime import datetime, timezone

import httpx
import pytest

from app.models import ProviderName, ProviderStatus
from app.providers import USGSProvider
from app.datetime_utils import parse_utc_datetime
from app.services import IncidentRepository, SyncService, deduplicate


def test_conservative_deduplication(incident_factory):
    usgs = incident_factory("us1", ProviderName.USGS)
    gdacs = incident_factory("gd1", ProviderName.GDACS, lat=10.05, lon=20.05, minutes=5)
    far = incident_factory("gd2", ProviderName.GDACS, lat=20, lon=30, minutes=5)
    merged = deduplicate([usgs, gdacs, far])
    assert len(merged) == 2
    assert any(len(item.sources) == 2 for item in merged)


def test_deduplication_normalizes_mixed_naive_and_aware_datetimes(incident_factory):
    aware = incident_factory("aware", ProviderName.USGS, minutes=0)
    naive = incident_factory("naive", ProviderName.GDACS, lat=10.01, lon=20.01, minutes=5)
    # Reproduce a legacy/malformed cached object that bypasses model validation.
    object.__setattr__(naive, "started_at", datetime(2026, 8, 29, 12, 5))
    object.__setattr__(naive, "updated_at", datetime(2026, 8, 29, 12, 6))
    object.__setattr__(naive.sources[0], "updated_at", datetime(2026, 8, 29, 12, 6))
    aware.updated_at = datetime(2026, 8, 29, 12, 7, tzinfo=timezone.utc)

    result = deduplicate([naive, aware])

    assert len(result) == 1
    assert len(result[0].sources) == 2
    assert result[0].started_at.utcoffset().total_seconds() == 0
    assert result[0].updated_at.utcoffset().total_seconds() == 0
    assert all(source.updated_at.utcoffset().total_seconds() == 0 for source in result[0].sources)


def test_timestamp_with_offset_is_converted_to_utc():
    value = parse_utc_datetime("2026-08-29T14:00:00+02:00")
    assert value == datetime(2026, 8, 29, 12, tzinfo=timezone.utc)
    assert value.tzinfo is timezone.utc


def test_provider_sync_timestamps_are_normalized_on_creation_and_assignment():
    status = ProviderStatus(provider=ProviderName.USGS, status="LIVE", lastAttempt=datetime(2026, 8, 29, 12))
    assert status.last_attempt.tzinfo is timezone.utc
    status.last_successful_sync = datetime(2026, 8, 29, 14, tzinfo=timezone.utc)
    assert status.last_successful_sync.tzinfo is timezone.utc


@pytest.mark.asyncio
async def test_provider_failure_keeps_last_known_good(incident_factory):
    repository = IncidentRepository()
    repository.replace_provider(ProviderName.USGS, [incident_factory()])
    transport = httpx.MockTransport(lambda _: httpx.Response(503))
    async with httpx.AsyncClient(transport=transport) as client:
        service = SyncService([USGSProvider(client)], repository)
        await service.sync_all()
    assert service.statuses[ProviderName.USGS].status == "DEGRADED"
    assert len(repository.all()) == 1

