import httpx
import pytest

from app.models import ProviderName
from app.providers import USGSProvider
from app.services import IncidentRepository, SyncService, deduplicate


def test_conservative_deduplication(incident_factory):
    usgs = incident_factory("us1", ProviderName.USGS)
    gdacs = incident_factory("gd1", ProviderName.GDACS, lat=10.05, lon=20.05, minutes=5)
    far = incident_factory("gd2", ProviderName.GDACS, lat=20, lon=30, minutes=5)
    merged = deduplicate([usgs, gdacs, far])
    assert len(merged) == 2
    assert any(len(item.sources) == 2 for item in merged)


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

