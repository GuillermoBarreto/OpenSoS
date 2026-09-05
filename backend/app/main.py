import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .models import IncidentCollection, IncidentStatus, IncidentType, ProviderName, Severity
from .providers import EONETProvider, GDACSProvider, USGSProvider
from .services import IncidentRepository, SyncService
from .datetime_utils import ensure_utc
from .intelligence.provider import OpenAIProvider
from .intelligence.service import IntelligenceError, IntelligenceService

settings = get_settings()
client = httpx.AsyncClient(timeout=settings.provider_timeout_seconds, follow_redirects=True, headers={"User-Agent": "OpenSoS/1.0 (+https://github.com/GuillermoBarreto/OpenSoS)"})
repository = IncidentRepository()
sync_service = SyncService([USGSProvider(client), EONETProvider(client), GDACSProvider(client)], repository)


def create_intelligence_service() -> IntelligenceService:
    if settings.ai_provider.casefold() == "openai" and settings.ai_api_key:
        return IntelligenceService(
            OpenAIProvider(settings.ai_api_key, settings.ai_model, settings.ai_timeout_seconds),
            settings.ai_timeout_seconds,
            max_concurrent_requests=settings.ai_max_concurrent_requests,
        )
    return IntelligenceService(None, settings.ai_timeout_seconds)


intelligence_service = create_intelligence_service()


async def sync_loop(provider, interval: int):
    while True:
        await sync_service.sync_provider(provider)
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_: FastAPI):
    intervals = [settings.usgs_sync_seconds, settings.eonet_sync_seconds, settings.gdacs_sync_seconds]
    tasks = [asyncio.create_task(sync_loop(provider, interval)) for provider, interval in zip(sync_service.providers, intervals)]
    yield
    for task in tasks: task.cancel()
    await client.aclose()


app = FastAPI(title="OpenSoS API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.exception_handler(IntelligenceError)
async def intelligence_error_handler(_, exc: IntelligenceError):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.get("/health")
async def health(): return {"status": "ok", "environment": settings.app_env}


def parse_bbox(value: str | None):
    if value is None: return None
    try: parts = [float(item) for item in value.split(",")]
    except ValueError: raise HTTPException(422, "bbox must contain four numbers")
    if len(parts) != 4: raise HTTPException(422, "bbox must be minLon,minLat,maxLon,maxLat")
    min_lon, min_lat, max_lon, max_lat = parts
    if not (-180 <= min_lon < max_lon <= 180 and -90 <= min_lat < max_lat <= 90):
        raise HTTPException(422, "bbox coordinates are invalid or unordered")
    return parts


@app.get("/api/incidents", response_model=IncidentCollection, response_model_by_alias=True)
async def incidents(type: IncidentType | None = None, severity: Severity | None = None,
                    status: IncidentStatus | None = None, provider: ProviderName | None = None,
                    start: datetime | None = None, end: datetime | None = None, bbox: str | None = None,
                    search: str | None = Query(None, max_length=100), limit: int = Query(1000, ge=1, le=5000)):
    bounds = parse_bbox(bbox)
    if start and end and ensure_utc(start) > ensure_utc(end):
        raise HTTPException(422, "start must be before or equal to end")
    values = repository.all()
    if type: values = [i for i in values if i.type == type]
    if severity: values = [i for i in values if i.severity == severity]
    if status: values = [i for i in values if i.status == status]
    if provider: values = [i for i in values if any(s.provider == provider for s in i.sources)]
    if start:
        start = ensure_utc(start)
        values = [i for i in values if i.started_at >= start]
    if end:
        end = ensure_utc(end)
        values = [i for i in values if i.started_at <= end]
    if bounds:
        values = [i for i in values if bounds[0] <= i.location.longitude <= bounds[2] and bounds[1] <= i.location.latitude <= bounds[3]]
    if search:
        term = search.casefold()
        values = [i for i in values if term in " ".join([i.id, i.title, i.description or "", *i.external_ids, *(s.provider.value for s in i.sources)]).casefold()]
    sync_service.refresh_ages()
    return IncidentCollection(incidents=values[:limit], total=len(values), generatedAt=datetime.now(timezone.utc), providers=list(sync_service.statuses.values()))


@app.get("/api/incidents/summary")
async def summary():
    values = repository.all()
    return {"total": len(values), "active": sum(i.status == IncidentStatus.ACTIVE for i in values),
            "highSeverity": sum(i.severity in (Severity.HIGH, Severity.CRITICAL) for i in values),
            "providersLive": sum(s.status == "LIVE" for s in sync_service.statuses.values()),
            "updatedAt": max((i.updated_at for i in values), default=None)}


@app.get("/api/providers/status", response_model=list, response_model_by_alias=True)
async def provider_status():
    sync_service.refresh_ages()
    return [item.model_dump(by_alias=True, mode="json") for item in sync_service.statuses.values()]


@app.get("/api/incidents/{incident_id}")
async def incident(incident_id: str):
    found = next((item for item in repository.all() if item.id == incident_id), None)
    if not found: raise HTTPException(404, "Incident not found")
    return found.model_dump(by_alias=True, mode="json")


@app.get("/api/intelligence/status")
async def intelligence_status():
    provider = intelligence_service.provider
    return {"available": intelligence_service.available, "configured": intelligence_service.available,
            "provider": provider.name if provider else None, "model": provider.model if provider else None}


@app.post("/api/intelligence/incidents/{incident_id}/brief")
async def incident_brief(incident_id: str):
    found = next((item for item in repository.all() if item.id == incident_id), None)
    if not found:
        raise IntelligenceError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
    brief = await intelligence_service.generate(found)
    return brief.model_dump(by_alias=True, mode="json")
