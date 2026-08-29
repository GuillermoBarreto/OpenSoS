import { useEffect, useMemo, useState } from 'react'
import { Analytics } from '@vercel/analytics/react'
import { IncidentMap } from './IncidentMap'
import type { Incident, IncidentCollection, IncidentType, ProviderStatus, Severity } from './types'
import './App.css'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TYPES: { label: string; value: IncidentType | 'ALL' }[] = [
  { label: 'All events', value: 'ALL' }, { label: 'Earthquakes', value: 'EARTHQUAKE' }, { label: 'Wildfires', value: 'WILDFIRE' },
  { label: 'Cyclones', value: 'TROPICAL_CYCLONE' }, { label: 'Floods', value: 'FLOOD' }, { label: 'Volcanoes', value: 'VOLCANO' }, { label: 'Other', value: 'OTHER' },
]
const relativeTime = (date: string) => { const seconds = Math.round((new Date(date).getTime() - Date.now()) / 1000); const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' }); if (Math.abs(seconds) < 3600) return formatter.format(Math.round(seconds / 60), 'minute'); if (Math.abs(seconds) < 86400) return formatter.format(Math.round(seconds / 3600), 'hour'); return formatter.format(Math.round(seconds / 86400), 'day') }

function ProviderPill({ provider }: { provider: ProviderStatus }) {
  return <span className={`provider provider--${provider.status.toLowerCase()}`} title={provider.lastError || ''}><span aria-hidden="true" />{provider.provider.replace('NASA ', '')} {provider.status}</span>
}
function Inspector({ incident, onClose }: { incident: Incident; onClose: () => void }) {
  const metrics = Object.entries(incident.metrics).filter(([, value]) => value !== null && value !== undefined && value !== '')
  return <aside className="inspector" aria-label="Selected incident" aria-live="polite">
    <button className="close" onClick={onClose} aria-label="Close incident details">×</button><p className="eyebrow">Selected event · {incident.type.replaceAll('_', ' ')}</p>
    <h2>{incident.title}</h2><p className="place">{incident.location.placeName || incident.location.country || 'Location unavailable'}</p>
    <span className={`severity severity--${incident.severity.toLowerCase()}`}>{incident.severity} severity</span>
    <dl className="facts"><div><dt>Occurred</dt><dd>{relativeTime(incident.startedAt)}</dd></div><div><dt>Updated</dt><dd>{relativeTime(incident.updatedAt)}</dd></div>
      {metrics.map(([key, value]) => <div key={key}><dt>{key.replace(/([A-Z])/g, ' $1')}</dt><dd>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}</dd></div>)}</dl>
    {incident.description && <section><h3>Details</h3><p>{incident.description}</p></section>}
    <section><h3>Sources</h3>{incident.sources.map(source => <a className="source" key={`${source.provider}-${source.externalId}`} href={source.url} target="_blank" rel="noreferrer"><strong>{source.provider}</strong><span>{source.externalId} · updated {relativeTime(source.updatedAt)}</span></a>)}</section>
  </aside>
}
export default function App() {
  const [data, setData] = useState<IncidentCollection | null>(null), [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState(() => new URLSearchParams(location.search).get('incident'))
  const [type, setType] = useState<IncidentType | 'ALL'>('ALL'), [severity, setSeverity] = useState<Severity | 'ALL'>('ALL'), [provider, setProvider] = useState('ALL'), [query, setQuery] = useState('')
  useEffect(() => { const controller = new AbortController(); fetch(`${API}/api/incidents?limit=5000`, { signal: controller.signal }).then(response => { if (!response.ok) throw new Error(`API returned ${response.status}`); return response.json() }).then(setData).catch(reason => { if (reason.name !== 'AbortError') setError(reason.message) }); return () => controller.abort() }, [])
  const incidents = useMemo(() => (data?.incidents || []).filter(item => (type === 'ALL' || item.type === type) && (severity === 'ALL' || item.severity === severity) && (provider === 'ALL' || item.sources.some(source => source.provider === provider)) && (!query || [item.title, item.description, item.id, ...item.externalIds].join(' ').toLowerCase().includes(query.toLowerCase()))), [data, type, severity, provider, query])
  const selected = data?.incidents.find(item => item.id === selectedId) || null
  const selectIncident = (id: string | null) => { setSelectedId(id); const url = new URL(location.href); if (id) url.searchParams.set('incident', id); else url.searchParams.delete('incident'); history.replaceState({}, '', url) }
  const high = incidents.filter(item => ['HIGH', 'CRITICAL'].includes(item.severity)).length
  return <main className={selected ? 'app app--selected' : 'app'}>
    <header className="topbar"><a className="brand" href="/" aria-label="OpenSoS home"><span>OPEN</span>SOS <small>Open Source for Society</small></a><nav aria-label="Primary"><a href="#map">Live events</a><a href="#about">About</a></nav><time dateTime={new Date().toISOString()}>{new Date().toLocaleString('en-GB', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', hour12: false })} UTC</time></header>
    <section className="telemetry" aria-live="polite">{!data && !error && <span>SYNCING GLOBAL EVENT DATA <i>USGS</i> <i>NASA EONET</i> <i>GDACS</i></span>}{error && <span className="error">Unable to reach the OpenSoS API · {error}</span>}{data && <><strong>{incidents.length} ACTIVE EVENTS</strong><span>{high} HIGH SEVERITY</span><span>{data.providers.filter(p => p.status === 'LIVE').length} PROVIDERS ONLINE</span><span>UPDATED {relativeTime(data.generatedAt)}</span></>}<div className="provider-list">{data?.providers.map(item => <ProviderPill key={item.provider} provider={item} />)}</div></section>
    <section className="map-stage" id="map"><IncidentMap incidents={incidents} selectedId={selectedId} onSelect={id => selectIncident(id)} /><div className="search"><label htmlFor="event-search">Search incidents</label><input id="event-search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Japan, hurricane, M6.5, event ID…" /></div>{selected && <Inspector incident={selected} onClose={() => selectIncident(null)} />}</section>
    <form className="filters" aria-label="Incident filters"><div className="type-filters">{TYPES.map(item => <button type="button" aria-pressed={type === item.value} key={item.value} onClick={() => setType(item.value)}>{item.label}</button>)}</div><label>Severity<select value={severity} onChange={e => setSeverity(e.target.value as Severity | 'ALL')}><option>ALL</option><option>CRITICAL</option><option>HIGH</option><option>MODERATE</option><option>LOW</option><option>INFO</option></select></label><label>Source<select value={provider} onChange={e => setProvider(e.target.value)}><option>ALL</option><option>USGS</option><option>NASA EONET</option><option>GDACS</option></select></label></form>
    <footer id="about">OpenSoS aggregates information from public data providers for situational awareness. Information may be delayed, incomplete, or revised. OpenSoS is not an emergency dispatch service. Map © OpenStreetMap contributors.</footer>
    <Analytics />
  </main>
}
