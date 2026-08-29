from fastapi.testclient import TestClient

from app.main import app, repository, sync_service
from app.models import ProviderName


def test_filter_search_bbox_and_lookup(incident_factory):
    item = incident_factory()
    repository.replace_provider(ProviderName.USGS, [item])
    client = TestClient(app)
    response = client.get("/api/incidents", params={"type": "EARTHQUAKE", "severity": "HIGH", "search": "Test Region", "bbox": "19,9,21,11"})
    assert response.status_code == 200 and response.json()["total"] == 1
    assert client.get(f"/api/incidents/{item.id}").status_code == 200
    assert client.get("/api/incidents/missing").status_code == 404


def test_bbox_validation():
    client = TestClient(app)
    assert client.get("/api/incidents?bbox=1,2,3").status_code == 422
    assert client.get("/api/incidents?bbox=20,10,10,30").status_code == 422
