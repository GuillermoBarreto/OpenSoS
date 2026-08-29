from fastapi.testclient import TestClient

from app.main import app, repository, sync_service
from app.models import ProviderName
from app.providers import EONETProvider, GDACSProvider, USGSProvider


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


def test_production_incident_call_with_all_provider_fixtures():
    client_stub = None
    usgs = USGSProvider(client_stub).normalize({"features": [{"id": "mixed-usgs", "geometry": {"type": "Point", "coordinates": [140, 35, 10]}, "properties": {"mag": 5, "place": "Japan", "time": 1788000000000, "updated": 1788000060000, "url": "https://earthquake.usgs.gov/event/mixed-usgs"}}]})
    eonet = EONETProvider(client_stub).normalize({"features": [{"id": "mixed-eonet", "geometry": {"type": "Point", "coordinates": [-120, 40]}, "properties": {"title": "Fixture Fire", "date": "2026-08-20T00:00:00", "categories": [{"id": "wildfires"}], "sources": [{"url": "https://example.com/fire"}]}}]})
    gdacs = GDACSProvider(client_stub).normalize({"features": [{"geometry": {"type": "Point", "coordinates": [122, 14]}, "properties": {"eventid": 9001, "eventtype": "TC", "name": "Fixture Cyclone", "fromdate": "2026-08-27T00:00:00", "datemodified": "2026-08-29T00:00:00", "alertlevel": "Orange", "url": {"report": "https://www.gdacs.org/report.aspx?id=9001"}}}]})
    repository.replace_provider(ProviderName.USGS, usgs)
    repository.replace_provider(ProviderName.EONET, eonet)
    repository.replace_provider(ProviderName.GDACS, gdacs)

    response = TestClient(app).get("/api/incidents?limit=5000")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    for incident in response.json()["incidents"]:
        assert incident["startedAt"].endswith("Z")
        assert incident["updatedAt"].endswith("Z")
