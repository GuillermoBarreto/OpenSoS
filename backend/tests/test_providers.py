import httpx

from app.models import IncidentType, Severity
from app.providers import EONETProvider, GDACSProvider, USGSProvider, earthquake_severity, gdacs_severity

client = httpx.AsyncClient()


def test_usgs_parsing():
    payload = {"features": [{"id": "us1", "geometry": {"type": "Point", "coordinates": [140, 35, 38]},
        "properties": {"mag": 6.7, "place": "Japan", "time": 1788000000000, "updated": 1788000060000,
                       "url": "https://earthquake.usgs.gov/event/us1", "felt": 12, "alert": "orange", "sig": 720, "tsunami": 1, "status": "reviewed"}}]}
    item = USGSProvider(client).normalize(payload)[0]
    assert item.id == "usgs-us1" and item.severity == Severity.HIGH
    assert item.started_at.tzinfo is not None and item.updated_at.tzinfo is not None
    assert item.sources[0].updated_at.tzinfo is not None
    assert item.metrics["depthKm"] == 38 and item.metrics["tsunami"] is True
    assert item.sources[0].original_severity == "orange"


def test_eonet_parsing_and_source_preservation():
    payload = {"features": [{"id": "EONET_1", "geometry": {"type": "Point", "coordinates": [-120, 40]},
        "properties": {"title": "Example Fire", "geometryDates": ["2026-08-20T00:00:00"], "closed": "2026-08-21T00:00:00",
                       "categories": [{"id": "wildfires", "title": "Wildfires"}],
                       "sources": [{"id": "EO", "url": "https://example.com/fire"}]}}]}
    item = EONETProvider(client).normalize(payload)[0]
    assert item.type == IncidentType.WILDFIRE and item.sources[0].url.host == "example.com"
    assert item.started_at.tzinfo is not None and item.updated_at.tzinfo is not None
    assert item.ended_at is not None and item.ended_at.tzinfo is not None
    assert item.sources[0].updated_at.tzinfo is not None
    assert item.metrics["category"] == "wildfires"


def test_gdacs_parsing_and_alert_mapping():
    payload = {"features": [{"geometry": {"type": "Point", "coordinates": [122, 14]}, "properties": {
        "eventid": 1001, "eventtype": "TC", "name": "Cyclone Ada", "country": "Philippines",
        "fromdate": "2026-08-27T00:00:00", "datemodified": "2026-08-29T00:00:00", "alertlevel": "Red",
        "url": {"report": "https://www.gdacs.org/report.aspx?id=1001"}}}]}
    item = GDACSProvider(client).normalize(payload)[0]
    assert item.type == IncidentType.TROPICAL_CYCLONE and item.severity == Severity.CRITICAL
    assert item.started_at.tzinfo is not None and item.updated_at.tzinfo is not None
    assert item.sources[0].updated_at.tzinfo is not None
    assert item.sources[0].original_severity == "Red"


def test_gdacs_invalid_report_link_uses_official_fallback():
    payload = {"features": [{"geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": {
        "eventid": 2, "eventtype": "FL", "name": "Flood", "fromdate": "2026-08-27T00:00:00Z",
        "alertlevel": "Green", "url": {"report": "no reportlink found"}}}]}
    item = GDACSProvider(client).normalize(payload)[0]
    assert item.sources[0].url.host == "www.gdacs.org"


def test_severity_boundaries():
    assert earthquake_severity(7) == Severity.CRITICAL
    assert earthquake_severity(6) == Severity.HIGH
    assert earthquake_severity(4.5) == Severity.MODERATE
    assert gdacs_severity("orange") == Severity.HIGH
