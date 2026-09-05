import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

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


@pytest.mark.asyncio
async def test_slow_provider_does_not_block_other_providers(incident_factory):
    started, release = asyncio.Event(), asyncio.Event()

    async def slow_fetch():
        started.set()
        await release.wait()
        return []

    slow = AsyncMock(name=ProviderName.GDACS)
    slow.name = ProviderName.GDACS
    slow.fetch.side_effect = slow_fetch
    fast = AsyncMock()
    fast.name = ProviderName.USGS
    fast.fetch.return_value = [incident_factory()]
    repository = IncidentRepository()
    service = SyncService([slow, fast], repository)
    task = asyncio.create_task(service.sync_provider(slow))
    try:
        await asyncio.wait_for(started.wait(), timeout=1)
        await asyncio.wait_for(service.sync_provider(fast), timeout=1)
        assert not task.done()
        assert service.statuses[ProviderName.USGS].status == "LIVE"
        assert len(repository.all()) == 1
    finally:
        release.set()
        await task


@pytest.mark.asyncio
async def test_bulk_and_individual_syncs_serialize_same_provider():
    started, release = asyncio.Event(), asyncio.Event()

    async def fetch():
        started.set()
        await release.wait()
        return []

    provider = AsyncMock()
    provider.name = ProviderName.USGS
    provider.fetch.side_effect = fetch
    service = SyncService([provider], IncidentRepository())
    individual = asyncio.create_task(service.sync_provider(provider))
    bulk = None
    try:
        await asyncio.wait_for(started.wait(), timeout=1)
        bulk = asyncio.create_task(service.sync_all())
        # Let both the bulk task and its gathered provider task run.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert provider.fetch.await_count == 1
    finally:
        release.set()
        await individual
        if bulk is not None:
            await bulk
    assert provider.fetch.await_count == 2


@pytest.mark.asyncio
async def test_successful_sync_records_completion_time(monkeypatch):
    attempt = datetime(2026, 8, 29, 12, tzinfo=timezone.utc)
    completed = datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc)

    class Clock:
        current = attempt

        @classmethod
        def now(cls, tz):
            return cls.current

    async def fetch():
        Clock.current = completed
        return []

    monkeypatch.setattr("app.services.datetime", Clock)
    provider = AsyncMock()
    provider.name = ProviderName.USGS
    provider.fetch.side_effect = fetch
    service = SyncService([provider], IncidentRepository())
    await service.sync_provider(provider)
    status = service.statuses[ProviderName.USGS]
    assert status.last_attempt == attempt
    assert status.last_successful_sync == completed
    assert status.data_age_seconds == 0

