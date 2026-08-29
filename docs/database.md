# Database decision

Milestone 1 intentionally has no database. Snapshots are process-local cache entries behind `IncidentRepository`, keeping the read-only deployment honest.

Milestone 2 should evaluate PostgreSQL/PostGIS for `incidents`, `incident_sources`, and `provider_syncs`, plus GiST indexes on point/full geometry. Add durable snapshots before multiple backend replicas.
