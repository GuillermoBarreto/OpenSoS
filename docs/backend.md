# Backend

From `backend/`, run `uvicorn app.main:app --reload`. Adapters are in `app/providers.py`, models in `app/models.py`, cache/deduplication in `app/services.py`, configuration in `app/config.py`, and routes/lifecycle in `app/main.py`.

USGS defaults to 60-second refresh; EONET and GDACS to 15 minutes. Independent loops prevent over-fetching. Failed syncs retain the last good snapshot and publish the truncated error.

Optional incident briefs live in `app/intelligence/`. Business logic uses the `AIProvider` interface; the initial OpenAI adapter is configured only through backend environment variables. Missing AI configuration does not affect startup, syncing, or incident routes.
