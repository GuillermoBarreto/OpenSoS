from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest

from app.models import Incident, IncidentSource, IncidentStatus, IncidentType, Location, ProviderName, Severity


@pytest.fixture
def incident_factory():
    def make(identifier="one", provider=ProviderName.USGS, lat=10, lon=20, minutes=0):
        time = datetime(2026, 8, 29, 12, minutes, tzinfo=timezone.utc)
        return Incident(id=f"{provider.value}-{identifier}", externalIds=[identifier], type=IncidentType.EARTHQUAKE,
            title="M6.1 earthquake — Test Region", severity=Severity.HIGH, status=IncidentStatus.ACTIVE,
            location=Location(latitude=lat, longitude=lon, placeName="Test Region"), startedAt=time, updatedAt=time,
            sources=[IncidentSource(provider=provider, externalId=identifier, url="https://example.com/event", updatedAt=time)],
            metrics={"magnitude": 6.1})
    return make

