import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'

vi.mock('./IncidentMap', () => ({ IncidentMap: ({ incidents, onSelect, onPreview }: { incidents: typeof response.incidents; onSelect: (id: string) => void; onPreview: (item: typeof incident | null) => void }) => <div aria-label="Mock map">{incidents.map(item => <button key={item.id} onMouseEnter={() => onPreview(item)} onFocus={() => onPreview(item)} onClick={() => onSelect(item.id)}>{item.title}</button>)}</div> }))
const incident = { id: 'usgs-test', externalIds: ['test'], type: 'EARTHQUAKE', title: 'M6.7 earthquake — Japan', severity: 'HIGH', status: 'ACTIVE', location: { latitude: 35, longitude: 140, placeName: 'Japan' }, startedAt: '2026-08-29T10:00:00Z', updatedAt: '2026-08-29T10:05:00Z', sources: [{ provider: 'USGS', externalId: 'test', url: 'https://earthquake.usgs.gov/test', updatedAt: '2026-08-29T10:05:00Z' }], metrics: { magnitude: 6.7, depthKm: 38 }, provenance: {}, createdAt: '2026-08-29T10:00:00Z' }
const secondIncident = { ...incident, id: 'usgs-second', externalIds: ['second'], title: 'M5.2 earthquake — Chile', location: { latitude: -33, longitude: -71, placeName: 'Chile' } }
const response = { incidents: [incident], total: 1, generatedAt: '2026-08-29T10:06:00Z', providers: [{ provider: 'USGS', status: 'LIVE', incidentCount: 1 }, { provider: 'GDACS', status: 'DEGRADED', lastError: 'timeout', incidentCount: 0 }] }
const aiBrief = { headline: 'Earthquake near Japan', summary: 'A magnitude 6.7 earthquake is reported near Japan.', keyPoints: ['USGS reports a depth of 38 km.'], sourcesUsed: ['USGS'], generatedAt: '2026-08-29T10:07:00Z', cached: false }
const mockAI = (post: () => Promise<unknown> = async () => ({ ok: true, json: async () => aiBrief }), available = true) => vi.stubGlobal('fetch', vi.fn((input: string | URL, options?: RequestInit) => {
  const url = String(input)
  if (url.includes('/api/intelligence/status')) return Promise.resolve({ ok: true, json: async () => ({ available, configured: available, provider: available ? 'openai' : null, model: available ? 'test' : null }) })
  if (options?.method === 'POST') return post()
  return Promise.resolve({ ok: true, json: async () => response })
}))

beforeEach(() => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(response) })); history.replaceState({}, '', '/') })
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('shows loading then real provider state and telemetry', async () => {
  render(<App />); expect(screen.getByText(/waking opensos data service/i)).toBeInTheDocument()
  expect(await screen.findByText(/1 visible events/i)).toBeInTheDocument(); expect(screen.getByText(/GDACS DEGRADED/i)).toBeInTheDocument()
})
test('filters, selects, attributes, and deep links an event', async () => {
  const user = userEvent.setup(); render(<App />); await screen.findByText(/1 visible events/i)
  await user.type(screen.getByLabelText(/search incidents/i), 'missing'); expect(screen.getByText(/0 visible events/i)).toBeInTheDocument()
  await user.clear(screen.getByLabelText(/search incidents/i)); await user.click(screen.getByRole('button', { name: /M6.7 earthquake/i }))
  expect(screen.getByLabelText(/selected incident/i)).toBeInTheDocument(); expect(screen.getByRole('link', { name: /USGS/i })).toHaveAttribute('href', expect.stringContaining('usgs.gov'))
  await waitFor(() => expect(location.search).toBe('?incident=usgs-test'))
})
test('restores selection from a shareable URL', async () => {
  history.replaceState({}, '', '/?incident=usgs-test'); render(<App />); expect(await screen.findByLabelText(/selected incident/i)).toBeInTheDocument()
})

test('legend explains event types, severity, and map states', async () => {
  const user = userEvent.setup(); render(<App />); await screen.findByText(/1 visible events/i)
  await user.click(screen.getByRole('button', { name: /map legend/i }))
  expect(screen.getAllByText('Earthquake').length).toBeGreaterThan(0); expect(screen.getAllByText(/critical/i).length).toBeGreaterThan(0); expect(screen.getByText(/Selected/)).toBeInTheDocument()
})

test('type, severity, and time filters use loaded incident data', async () => {
  const user = userEvent.setup(); render(<App />); await screen.findByText(/1 visible events/i)
  expect(screen.getByRole('button', { name: /Earthquake 1/i })).toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('Severity'), 'CRITICAL'); expect(screen.getByText(/0 visible events/i)).toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('Severity'), 'ALL'); await user.selectOptions(screen.getByLabelText('Time range'), '1h'); expect(screen.getByText(/0 visible events/i)).toBeInTheDocument()
})

test('event focus opens an equivalent hover preview', async () => {
  render(<App />); await screen.findByText(/1 visible events/i)
  const event = screen.getByRole('button', { name: /M6.7 earthquake/i }); fireEvent.focus(event)
  expect(screen.getByText(/Updated/)).toBeInTheDocument(); expect(screen.getByText(/HIGH · USGS/)).toBeInTheDocument()
})

test('provider status opens sanitized operational details', async () => {
  const user = userEvent.setup(); render(<App />); await screen.findByText(/1 visible events/i)
  await user.click(screen.getByRole('button', { name: /GDACS DEGRADED/i }))
  expect(screen.getByText(/Provider synchronization timed out/i)).toBeInTheDocument(); expect(screen.getByRole('link', { name: /Official source/i })).toHaveAttribute('href', 'https://www.gdacs.org')
})

test('shows a Render cold-start state before the request resolves', () => {
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {}))); render(<App />)
  expect(screen.getByText(/WAKING OPENSOS DATA SERVICE/i)).toBeInTheDocument(); expect(screen.getByText(/up to a minute/i)).toBeInTheDocument()
})

test('shows AI unavailable without hiding normal incident details', async () => {
  mockAI(undefined, false); const user = userEvent.setup(); render(<App />)
  await user.click(await screen.findByRole('button', { name: /M6.7 earthquake/i }))
  expect(await screen.findByText('AI brief unavailable')).toBeInTheDocument()
  expect(screen.getByText('Magnitude')).toBeInTheDocument(); expect(screen.getByRole('link', { name: /USGS/i })).toBeInTheDocument()
})

test('generates an accessible brief manually and displays sources used', async () => {
  let resolvePost!: (value: unknown) => void; mockAI(() => new Promise(resolve => { resolvePost = resolve }))
  const user = userEvent.setup(); render(<App />); await user.click(await screen.findByRole('button', { name: /M6.7 earthquake/i }))
  const generate = await screen.findByRole('button', { name: 'Generate AI brief' }); generate.focus(); expect(generate).toHaveFocus()
  await user.click(generate); expect(screen.getByText('GENERATING INCIDENT BRIEF')).toHaveAttribute('role', 'status')
  resolvePost({ ok: true, json: async () => aiBrief })
  expect(await screen.findByRole('heading', { name: 'Earthquake near Japan' })).toBeInTheDocument()
  expect(document.querySelector('.ai-sources')).toHaveTextContent('Sources used: USGS'); expect(screen.getByText(/may be incomplete/i)).toBeInTheDocument()
})

test('shows a safe provider error and supports manual retry', async () => {
  let calls = 0; mockAI(async () => ++calls === 1 ? { ok: false, json: async () => ({ error: { code: 'AI_UNAVAILABLE' } }) } : { ok: true, json: async () => aiBrief })
  const user = userEvent.setup(); render(<App />); await user.click(await screen.findByRole('button', { name: /M6.7 earthquake/i }))
  await user.click(await screen.findByRole('button', { name: 'Generate AI brief' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate brief right now.')
  await user.click(screen.getByRole('button', { name: 'Retry' })); expect(await screen.findByText(aiBrief.summary)).toBeInTheDocument(); expect(calls).toBe(2)
})

test('does not carry an AI brief into a newly selected incident', async () => {
  mockAI(); const user = userEvent.setup(); const twoIncidentResponse = { ...response, incidents: [incident, secondIncident], total: 2 }
  vi.mocked(fetch).mockImplementation((input: string | URL | Request, options?: RequestInit) => {
    const url = String(input)
    if (url.includes('/api/intelligence/status')) return Promise.resolve({ ok: true, json: async () => ({ available: true, configured: true }) } as Response)
    if (options?.method === 'POST') return Promise.resolve({ ok: true, json: async () => aiBrief } as Response)
    return Promise.resolve({ ok: true, json: async () => twoIncidentResponse } as Response)
  })
  render(<App />); await user.click(await screen.findByRole('button', { name: /M6.7 earthquake/i }))
  await user.click(await screen.findByRole('button', { name: 'Generate AI brief' }))
  expect(await screen.findByText(aiBrief.summary)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /M5.2 earthquake/i }))
  expect(screen.queryByText(aiBrief.summary)).not.toBeInTheDocument()
  expect(await screen.findByRole('button', { name: 'Generate AI brief' })).toBeInTheDocument()
})
