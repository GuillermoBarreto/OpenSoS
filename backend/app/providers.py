from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import httpx

from .models import Incident, IncidentSource, IncidentStatus, IncidentType, Location, ProviderName, Severity


def utc_from_ms(value: int | float) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def earthquake_severity(magnitude: float | None) -> Severity:
    if magnitude is None:
        return Severity.INFO
    if magnitude >= 7:
        return Severity.CRITICAL
    if magnitude >= 6:
        return Severity.HIGH
    if magnitude >= 4.5:
        return Severity.MODERATE
    if magnitude >= 2.5:
        return Severity.LOW
    return Severity.INFO


def gdacs_severity(alert: str | None) -> Severity:
    return {"RED": Severity.CRITICAL, "ORANGE": Severity.HIGH, "GREEN": Severity.LOW}.get((alert or "").upper(), Severity.INFO)


EONET_TYPES = {
    "wildfires": IncidentType.WILDFIRE, "severeStorms": IncidentType.SEVERE_WEATHER,
    "volcanoes": IncidentType.VOLCANO, "floods": IncidentType.FLOOD,
    "seaLakeIce": IncidentType.OTHER, "drought": IncidentType.DROUGHT,
}
GDACS_TYPES = {"EQ": IncidentType.EARTHQUAKE, "TC": IncidentType.TROPICAL_CYCLONE,
               "FL": IncidentType.FLOOD, "VO": IncidentType.VOLCANO, "DR": IncidentType.DROUGHT}


class Provider(ABC):
    name: ProviderName
    url: str

    def __init__(self, client: httpx.AsyncClient): self.client = client

    async def fetch(self) -> list[Incident]:
        response = await self.client.get(self.url)
        response.raise_for_status()
        return self.normalize(response.json())

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> list[Incident]: ...


class USGSProvider(Provider):
    name = ProviderName.USGS
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

    def normalize(self, payload: dict[str, Any]) -> list[Incident]:
        result = []
        for feature in payload.get("features", []):
            props, coords = feature.get("properties", {}), feature.get("geometry", {}).get("coordinates", [])
            if len(coords) < 2 or not feature.get("id") or not props.get("url"): continue
            mag = props.get("mag")
            started = utc_from_ms(props["time"])
            updated = utc_from_ms(props.get("updated", props["time"]))
            result.append(Incident(
                id=f"usgs-{feature['id']}", externalIds=[feature["id"]], type=IncidentType.EARTHQUAKE,
                title=f"M{mag if mag is not None else '?'} earthquake — {props.get('place') or 'Unknown location'}",
                severity=earthquake_severity(mag), status=IncidentStatus.ACTIVE if props.get("status") != "deleted" else IncidentStatus.ENDED,
                location=Location(latitude=coords[1], longitude=coords[0], placeName=props.get("place")),
                geometry=feature.get("geometry"), startedAt=started, updatedAt=updated,
                sources=[IncidentSource(provider=self.name, externalId=feature["id"], url=props["url"], updatedAt=updated, originalSeverity=props.get("alert"))],
                metrics={"magnitude": mag, "depthKm": coords[2] if len(coords) > 2 else None, "feltReports": props.get("felt"),
                         "alertLevel": props.get("alert"), "significance": props.get("sig"), "tsunami": bool(props.get("tsunami")), "providerStatus": props.get("status")},
                provenance={"provider": "USGS", "feed": self.url}, createdAt=started,
            ))
        return result


class EONETProvider(Provider):
    name = ProviderName.EONET
    url = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson?status=open&days=30&limit=500"

    def normalize(self, payload: dict[str, Any]) -> list[Incident]:
        result = []
        for feature in payload.get("features", []):
            props, geometry = feature.get("properties", {}), feature.get("geometry", {})
            event_id = feature.get("id") or props.get("id")
            categories = props.get("categories", [])
            category = categories[0].get("id") if categories and isinstance(categories[0], dict) else (categories[0] if categories else "")
            coords = geometry.get("coordinates", [])
            point = coords[-1] if geometry.get("type") == "LineString" and coords else coords
            if geometry.get("type") == "Polygon" and coords and coords[0]: point = coords[0][0]
            if not event_id or not isinstance(point, list) or len(point) < 2: continue
            started = parse_time(props.get("date") or (props.get("geometryDates") or [None])[0])
            sources = props.get("sources") or []
            link = props.get("link") or f"https://eonet.gsfc.nasa.gov/api/v3/events/{event_id}"
            result.append(Incident(
                id=f"eonet-{event_id}", externalIds=[event_id], type=EONET_TYPES.get(category, IncidentType.OTHER),
                title=props.get("title") or "NASA EONET event", description=props.get("description"), severity=Severity.INFO,
                status=IncidentStatus.ENDED if props.get("closed") else IncidentStatus.ACTIVE,
                location=Location(latitude=point[1], longitude=point[0], placeName=props.get("title")), geometry=geometry,
                startedAt=started, updatedAt=started, endedAt=parse_time(props["closed"]) if props.get("closed") else None,
                sources=[IncidentSource(provider=self.name, externalId=event_id, url=(sources[0].get("url") if sources else link) or link, updatedAt=started)],
                metrics={"magnitude": props.get("magnitudeValue"), "magnitudeUnit": props.get("magnitudeUnit"), "category": category},
                provenance={"provider": "NASA EONET", "curatedSources": sources, "feed": self.url}, createdAt=started,
            ))
        return result


class GDACSProvider(Provider):
    name = ProviderName.GDACS
    url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ;TC;FL;VO;DR&alertlevel=green;orange;red"

    def normalize(self, payload: dict[str, Any]) -> list[Incident]:
        result = []
        for feature in payload.get("features", []):
            props, geometry = feature.get("properties", {}), feature.get("geometry", {})
            event_id = str(props.get("eventid") or feature.get("id") or "")
            event_type = str(props.get("eventtype") or "").upper()
            coords = geometry.get("coordinates", [])
            if geometry.get("type") == "MultiPolygon" and coords: point = coords[0][0][0]
            elif geometry.get("type") == "Polygon" and coords: point = coords[0][0]
            else: point = coords
            if not event_id or not isinstance(point, list) or len(point) < 2: continue
            started = parse_time(props.get("fromdate") or props.get("datemodified"))
            updated = parse_time(props.get("datemodified") or props.get("fromdate"))
            alert = props.get("alertlevel")
            source_url = props.get("url", {}).get("report") if isinstance(props.get("url"), dict) else props.get("url")
            if not isinstance(source_url, str) or not source_url.startswith(("https://", "http://")):
                source_url = f"https://www.gdacs.org/report.aspx?eventid={event_id}&eventtype={event_type}"
            result.append(Incident(
                id=f"gdacs-{event_type.lower()}-{event_id}", externalIds=[event_id], type=GDACS_TYPES.get(event_type, IncidentType.OTHER),
                title=props.get("name") or props.get("eventname") or f"GDACS {event_type} event", severity=gdacs_severity(alert),
                status=IncidentStatus.ACTIVE, location=Location(latitude=point[1], longitude=point[0], country=props.get("country"), placeName=props.get("name")),
                geometry=geometry, startedAt=started, updatedAt=updated,
                sources=[IncidentSource(provider=self.name, externalId=event_id, url=source_url, updatedAt=updated, originalSeverity=alert)],
                metrics={"alertLevel": alert, "severityScore": props.get("severitydata", {}).get("severity") if isinstance(props.get("severitydata"), dict) else None,
                         "eventType": event_type}, provenance={"provider": "GDACS", "feed": self.url}, createdAt=started,
            ))
        return result
