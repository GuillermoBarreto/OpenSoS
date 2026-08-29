# Backend

From `backend/`, run `uvicorn app.main:app --reload`. Adapters are in `app/providers.py`, models in `app/models.py`, cache/deduplication in `app/services.py`, configuration in `app/config.py`, and routes/lifecycle in `app/main.py`.

USGS defaults to 60-second refresh; EONET and GDACS to 15 minutes. Independent loops prevent over-fetching. Failed syncs retain the last good snapshot and publish the truncated error.
