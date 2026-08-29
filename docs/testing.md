# Testing

Backend tests cover all provider parsers, severity boundaries, deduplication, failure fallback, query combinations, bbox validation, and lookup. HTTP is mocked.

Frontend tests cover loading, live/degraded states, search, selection, inspector content, attribution, and deep links. The map is replaced by a deterministic test double; MapLibre clustering is verified through builds/browser smoke tests.

For performance checks, generate local collections at 100, 1,000, and 5,000 points. Do not load-test official feeds.

Milestone 1.5A frontend coverage includes the collapsible legend, real category counts, type/severity/time filters, keyboard-equivalent preview, inspector/deep link, provider detail sanitization, and Render cold-start state. Deterministic 1,000, 2,500, and 5,000 incident fixtures exercise filtering without network or DOM marker creation.

Milestone 1.5B tests mock every AI call. Backend cases cover disabled/configured behavior, structured contracts, context grounding, source enforcement, safe errors, lookup failures, cache reuse/invalidation, and earthquake/wildfire/cyclone evaluation fixtures. Frontend cases cover unavailable, manual generation, loading, success, sources, failure/retry, accessible controls, and preservation of normal facts.
