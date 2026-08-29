# Testing

Backend tests cover all provider parsers, severity boundaries, deduplication, failure fallback, query combinations, bbox validation, and lookup. HTTP is mocked.

Frontend tests cover loading, live/degraded states, search, selection, inspector content, attribution, and deep links. The map is replaced by a deterministic test double; MapLibre clustering is verified through builds/browser smoke tests.

For performance checks, generate local collections at 100, 1,000, and 5,000 points. Do not load-test official feeds.
