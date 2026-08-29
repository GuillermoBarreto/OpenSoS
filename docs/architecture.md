# Architecture and incident model

Optional incident intelligence follows `React → FastAPI → IntelligenceService → AIProvider`. It consumes one normalized incident and attached provenance only; it does not alter provider ingestion or map rendering. See [intelligence](intelligence.md).

Provider adapters own fetching, validation, normalization, and provider-specific errors. `SyncService` writes successful snapshots through `IncidentRepository`; failed refreshes mark health `DEGRADED` but retain the prior snapshot. Routes consume only normalized incidents.

The typed model contains IDs, type, title/description, normalized severity/status, location, optional GeoJSON, UTC timestamps, sources, type-specific metrics, provenance, and creation time. Provider-only fields stay in metrics/provenance.

Supported types: earthquake, wildfire, tropical cyclone, flood, volcano, severe weather, tsunami, drought, and other.

## Severity normalization

Normalization is only for UI filtering; values are not scientifically equivalent. Original alerts remain in `sources[].originalSeverity` and metrics.

- USGS magnitude: `<2.5 INFO`, `2.5–4.49 LOW`, `4.5–5.99 MODERATE`, `6–6.99 HIGH`, `>=7 CRITICAL`.
- GDACS: `GREEN LOW`, `ORANGE HIGH`, `RED CRITICAL`, missing/unknown `INFO`.
- EONET: `INFO` unless a future documented category metric supports conservative mapping.

## Deduplication

Only cross-provider earthquakes within 30 km and 10 minutes merge. Same-provider records and other hazard types stay separate. Merges retain all IDs/sources and set `provenance.deduplicated`. This favors duplicates over false merges.

## Persistence

The in-memory repository is appropriate for this read-only milestone and is replaceable without pretending to be a database. PostGIS becomes justified with durable timelines/community reports; expected tables are `incidents`, `incident_sources`, `provider_syncs`, with GiST geometry indexes.
