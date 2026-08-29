import type { Incident, IncidentType, Severity } from './types'

export const EVENT_VISUALS: Record<IncidentType, { label: string; short: string; color: string; symbol: string }> = {
  EARTHQUAKE: { label: 'Earthquake', short: 'EQ', color: '#e9a23b', symbol: '◆' },
  WILDFIRE: { label: 'Wildfire', short: 'WF', color: '#ee6848', symbol: '▲' },
  TROPICAL_CYCLONE: { label: 'Cyclone', short: 'TC', color: '#aa82dd', symbol: '◉' },
  FLOOD: { label: 'Flood', short: 'FL', color: '#5ba7d9', symbol: '≈' },
  VOLCANO: { label: 'Volcano', short: 'VO', color: '#d8504f', symbol: '△' },
  SEVERE_WEATHER: { label: 'Severe weather', short: 'SW', color: '#dfc44f', symbol: '✦' },
  TSUNAMI: { label: 'Tsunami', short: 'TS', color: '#51c6cb', symbol: '≋' },
  DROUGHT: { label: 'Drought', short: 'DR', color: '#b99a58', symbol: '◇' },
  OTHER: { label: 'Other', short: 'OT', color: '#91a0a8', symbol: '●' },
}

export const SEVERITIES: Severity[] = ['INFO', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']
export const TYPE_ORDER = Object.keys(EVENT_VISUALS) as IncidentType[]
export type TimeRange = '1h' | '6h' | '24h' | '7d' | 'all'
export type Region = 'GLOBAL' | 'NORTH_AMERICA' | 'SOUTH_AMERICA' | 'EUROPE' | 'AFRICA' | 'ASIA' | 'OCEANIA'

export const relativeTime = (date: string) => {
  const seconds = Math.round((new Date(date).getTime() - Date.now()) / 1000)
  const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  if (Math.abs(seconds) < 3600) return formatter.format(Math.round(seconds / 60), 'minute')
  if (Math.abs(seconds) < 86400) return formatter.format(Math.round(seconds / 3600), 'hour')
  return formatter.format(Math.round(seconds / 86400), 'day')
}

export const isWithinTime = (incident: Incident, range: TimeRange, now = Date.now()) => {
  if (range === 'all') return true
  const milliseconds = { '1h': 3_600_000, '6h': 21_600_000, '24h': 86_400_000, '7d': 604_800_000 }[range]
  return new Date(incident.updatedAt).getTime() >= now - milliseconds
}
