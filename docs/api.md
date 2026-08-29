# HTTP API

- `GET /health` — application health, not provider health.
- `GET /api/incidents` — incidents plus provider state.
- `GET /api/incidents/{id}` — one incident or 404.
- `GET /api/incidents/summary` — real totals and freshness.
- `GET /api/providers/status` — attempts, success, error, age, count.

Incident queries accept enum `type`, `severity`, `status`, `provider`; ISO-8601 `start`/`end`; `search`; `limit` (1–5000); and `bbox=minLon,minLat,maxLon,maxLat`. Bad or unordered coordinates return 422. OpenAPI is at `/docs`.
