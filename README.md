# OpenSoS

**Open Source for Society** — global crisis intelligence, built in the open.

OpenSoS aggregates trusted public disaster information into one operational map. Milestone 1 answers: **what significant natural hazards and emergency events are happening around the world right now?** It preserves every source, reports provider freshness honestly, and remains useful when one provider fails.

OpenSoS is open source first, community driven, privacy first, transparent, accessible, and intentionally simple. It does not collect location, use tracking, or present itself as an original authority or emergency service.

## Architecture

- `frontend/`: React, TypeScript, Vite, MapLibre GL JS; map clustering, search, filters, responsive inspector, and incident deep links.
- `backend/`: FastAPI, Pydantic models, isolated USGS/EONET/GDACS adapters, provider-specific sync loops, last-known-good memory cache, filtering, and conservative deduplication.
- `docs/`: API, architecture, deployment, testing, and security decisions.

The backend uses an in-memory repository for Milestone 1. This is deliberate: there is no write workflow yet, and PostgreSQL/PostGIS would add deployment weight without improving the read-only feed. The repository boundary can be replaced when durable incident history and community reports arrive.

## Official data providers

| Provider | Endpoint | Use |
|---|---|---|
| USGS | `earthquake.usgs.gov/.../summary/all_day.geojson` | Past-day earthquakes |
| NASA EONET v3 | `eonet.gsfc.nasa.gov/api/v3/events/geojson` | Curated open natural events |
| GDACS | `gdacs.org/gdacsapi/api/events/geteventlist/SEARCH` | Global disaster alerts |

Source URLs and original alert values are retained. Map tiles are © OpenStreetMap contributors. See [architecture](docs/architecture.md) for normalization and [API](docs/api.md) for filters.

## Local development

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate; macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
npm ci
copy .env.example .env.local  # use cp on macOS/Linux
npm run dev
```

## Environment

- Frontend: `VITE_API_BASE_URL` (default `http://localhost:8000`).
- Backend: `APP_ENV`, comma-separated `CORS_ORIGINS`, `PROVIDER_TIMEOUT_SECONDS`, `USGS_SYNC_SECONDS`, `EONET_SYNC_SECONDS`, `GDACS_SYNC_SECONDS`.
- No provider secrets or API keys are required.

## Testing

```bash
cd backend && pytest
cd frontend && npm test && npm run lint && npm run build
```

Provider tests use fixtures or mocked HTTP; automated tests do not call official services.

## Deployment

Deploy `frontend/` to Vercel with `VITE_API_BASE_URL` set to the Render API URL. Deploy `backend/` using `backend/render.yaml`, setting `CORS_ORIGINS` to the Vercel origin. See [deployment notes](docs/deployment.md).

## Known limitations

- Cache is process-local and cold after restart; no history is retained.
- EONET generally has INFO severity because it has no equivalent alert scale.
- Deduplication only handles close, near-simultaneous cross-provider earthquakes.
- Polygon data is preserved by the API but not yet rendered for every provider.
- Public OpenStreetMap tiles are appropriate for development/modest traffic, not a high-volume SLA.

## Roadmap

- **Milestone 1 — Global crisis foundation:** official feeds, operational map, provenance, health, caching, filtering, and tests.
- **Milestone 2 — Community Reporting & Verification:** community submissions and transparent verification. Not implemented yet.
- Later: PostGIS history, public APIs, richer geospatial layers, and incident timelines.

## Disclaimer

OpenSoS aggregates information from public data providers for situational awareness. Information may be delayed, incomplete, or revised. OpenSoS is not an emergency dispatch service.

MIT licensed.
