import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'

vi.mock('./IncidentMap', () => ({ IncidentMap: ({ incidents, onSelect }: { incidents: { id: string; title: string }[]; onSelect: (id: string) => void }) => <div aria-label="Mock map">{incidents.map(item => <button key={item.id} onClick={() => onSelect(item.id)}>{item.title}</button>)}</div> }))
const incident = { id: 'usgs-test', externalIds: ['test'], type: 'EARTHQUAKE', title: 'M6.7 earthquake — Japan', severity: 'HIGH', status: 'ACTIVE', location: { latitude: 35, longitude: 140, placeName: 'Japan' }, startedAt: '2026-08-29T10:00:00Z', updatedAt: '2026-08-29T10:05:00Z', sources: [{ provider: 'USGS', externalId: 'test', url: 'https://earthquake.usgs.gov/test', updatedAt: '2026-08-29T10:05:00Z' }], metrics: { magnitude: 6.7, depthKm: 38 }, provenance: {}, createdAt: '2026-08-29T10:00:00Z' }
const response = { incidents: [incident], total: 1, generatedAt: '2026-08-29T10:06:00Z', providers: [{ provider: 'USGS', status: 'LIVE', incidentCount: 1 }, { provider: 'GDACS', status: 'DEGRADED', lastError: 'timeout', incidentCount: 0 }] }

beforeEach(() => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(response) })); history.replaceState({}, '', '/') })
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('shows loading then real provider state and telemetry', async () => {
  render(<App />); expect(screen.getByText(/syncing global event data/i)).toBeInTheDocument()
  expect(await screen.findByText(/1 active events/i)).toBeInTheDocument(); expect(screen.getByText(/GDACS DEGRADED/i)).toBeInTheDocument()
})
test('filters, selects, attributes, and deep links an event', async () => {
  const user = userEvent.setup(); render(<App />); await screen.findByText(/1 active events/i)
  await user.type(screen.getByLabelText(/search incidents/i), 'missing'); expect(screen.getByText(/0 active events/i)).toBeInTheDocument()
  await user.clear(screen.getByLabelText(/search incidents/i)); await user.click(screen.getByRole('button', { name: /M6.7 earthquake/i }))
  expect(screen.getByLabelText(/selected incident/i)).toBeInTheDocument(); expect(screen.getByRole('link', { name: /USGS/i })).toHaveAttribute('href', expect.stringContaining('usgs.gov'))
  await waitFor(() => expect(location.search).toBe('?incident=usgs-test'))
})
test('restores selection from a shareable URL', async () => {
  history.replaceState({}, '', '/?incident=usgs-test'); render(<App />); expect(await screen.findByLabelText(/selected incident/i)).toBeInTheDocument()
})
