# OpenSoS

**Open Source for Society** — global crisis intelligence, built in the open.

OpenSoS aggregates trusted public disaster information into one operational map. Milestone 1 answers: **what significant natural hazards and emergency events are happening around the world right now?** It preserves every source, reports provider freshness honestly, and remains useful when one provider fails.

OpenSoS is open source first, community driven, privacy first, transparent, accessible, and intentionally simple. It does not collect location, use tracking, or present itself as an original authority or emergency service.

## Architecture

- `frontend/`: React, TypeScript, Vite, MapLibre GL JS; map clustering, search, filters, responsive inspector, and incident deep links.
- `backend/`: FastAPI, Pydantic models, isolated USGS/EONET/GDACS adapters, provider-specific sync loops, last-known-good memory cache, filtering, and conservative deduplication.
- `docs/`: API, architecture, deployment, testing, and security decisions.

## Milestone 1.5B — Grounded incident briefs

Selected incidents can optionally receive a concise, manually requested AI brief. FastAPI constructs a minimal context from normalized incident facts and provenance, invokes a vendor-neutral intelligence service, validates structured output and source names, and caches unchanged briefs in memory. The map and inspector remain fully functional without AI configuration. See [intelligence](docs/intelligence.md).

## Milestone 1.5A — Map UX & Incident Experience

The map now distinguishes every incident type with a shared color and symbol language while severity independently controls marker size, stroke, and priority rings. Compact cluster previews expose type breakdowns and high/critical totals. A collapsible legend, real category counts, time filters, regional navigation, event previews, provider detail panels, and type-aware incident inspector make the live dataset easier to interpret.

Only the selected marker uses continuous animation, with high/critical events receiving static outer emphasis. Motion is disabled when `prefers-reduced-motion` is active. Rendering remains in MapLibre sources/layers—OpenSoS does not create thousands of DOM markers.

Render cold starts use staged retries at roughly 2, 5, and 10 seconds while clearly reporting that the data service is waking. Persistent failure becomes an explicit retryable error after the retry budget.

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
- Backend: `APP_ENV`, comma-separated `CORS_ORIGINS`, provider sync settings, and optional `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`, `AI_TIMEOUT_SECONDS`.
- Incident providers require no secrets. AI remains disabled unless its backend provider and key are configured.

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
- AI brief caching is process-local and is lost on restart or split across replicas.
- EONET generally has INFO severity because it has no equivalent alert scale.
- Deduplication only handles close, near-simultaneous cross-provider earthquakes.
- Polygon data is preserved by the API but not yet rendered for every provider.
- Public OpenStreetMap tiles are appropriate for development/modest traffic, not a high-volume SLA.

## Roadmap

- **Milestone 1 — Global crisis foundation:** official feeds, operational map, provenance, health, caching, filtering, and tests.
- **Milestone 1.5A — Map UX & Incident Experience:** visual language, cluster intelligence, time/region navigation, previews, provider transparency, and cold-start resilience.
- **Milestone 1.5B — AI Backend & Incident Briefs:** optional grounded summaries with validated provenance and explicit generation.
- **Milestone 2 — Community Reporting & Verification:** community submissions and transparent verification. Not implemented yet.
- Later: PostGIS history, public APIs, richer geospatial layers, and incident timelines.

## Disclaimer

OpenSoS aggregates information from public data providers for situational awareness. Information may be delayed, incomplete, or revised. OpenSoS is not an emergency dispatch service.

MIT licensed.
