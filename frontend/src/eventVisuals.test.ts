import { expect, test } from 'vitest'
import { EVENT_VISUALS, TYPE_ORDER, isWithinTime } from './eventVisuals'
import type { Incident } from './types'

const make = (index: number): Incident => ({ id: `event-${index}`, externalIds: [`${index}`], type: TYPE_ORDER[index % TYPE_ORDER.length], title: `Event ${index}`, severity: 'LOW', status: 'ACTIVE', location: { latitude: 0, longitude: 0 }, startedAt: new Date().toISOString(), updatedAt: new Date().toISOString(), sources: [], metrics: {}, provenance: {}, createdAt: new Date().toISOString() })

test('all incident types have distinct non-color symbols and labels', () => {
  expect(new Set(Object.values(EVENT_VISUALS).map(item => item.symbol)).size).toBe(TYPE_ORDER.length)
  expect(Object.values(EVENT_VISUALS).every(item => item.label && item.color)).toBe(true)
})

test.each([1000, 2500, 5000])('filters %i local incidents without changing the collection', count => {
  const incidents = Array.from({ length: count }, (_, index) => make(index)); const before = incidents.length
  const filtered = incidents.filter(item => item.type === 'EARTHQUAKE' && isWithinTime(item, '24h'))
  expect(filtered.length).toBeGreaterThan(0); expect(incidents).toHaveLength(before)
})
