import type { Geometry } from 'geojson'

export type IncidentType = 'EARTHQUAKE' | 'WILDFIRE' | 'TROPICAL_CYCLONE' | 'FLOOD' | 'VOLCANO' | 'SEVERE_WEATHER' | 'TSUNAMI' | 'DROUGHT' | 'OTHER'
export type Severity = 'INFO' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
export interface IncidentSource { provider: 'USGS' | 'NASA EONET' | 'GDACS'; externalId: string; url: string; updatedAt: string; originalSeverity?: string }
export interface Incident { id: string; externalIds: string[]; type: IncidentType; title: string; description?: string; severity: Severity; status: 'ACTIVE' | 'ENDED' | 'UNKNOWN'; location: { latitude: number; longitude: number; country?: string; region?: string; placeName?: string }; geometry?: Geometry; startedAt: string; updatedAt: string; endedAt?: string; sources: IncidentSource[]; metrics: Record<string, string | number | boolean | null>; provenance: Record<string, unknown>; createdAt: string }
export interface ProviderStatus { provider: string; status: 'LIVE' | 'DEGRADED' | 'SYNCING'; lastSuccessfulSync?: string; lastAttempt?: string; lastError?: string; dataAgeSeconds?: number; incidentCount: number }
export interface IncidentCollection { incidents: Incident[]; total: number; generatedAt: string; providers: ProviderStatus[] }
