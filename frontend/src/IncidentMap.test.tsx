import { act, cleanup, render } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import type { FeatureCollection } from 'geojson'
import type { Incident } from './types'

const state = vi.hoisted(() => ({ maps: [] as FakeMap[] }))
class FakeMap {
  handlers = new Map<string, (() => void)[]>()
  layers: Record<string, { id: string; type: string; layout?: Record<string, unknown> }> = {}
  data?: FeatureCollection
  source = { setData: vi.fn((data: FeatureCollection) => { this.data = data }) }
  loaded = vi.fn(() => false)
  options: { style: string }
  constructor(options: { style: string }) { this.options = options; state.maps.push(this) }
  on(event: string, ...args: unknown[]) {
    if (args.length === 1) this.handlers.set(event, [...(this.handlers.get(event) || []), args[0] as () => void])
  }
  once(event: string, handler: () => void) { this.on(event, handler) }
  fire(event: string) { this.handlers.get(event)?.forEach(handler => handler()) }
  addSource(_id: string, options: { data: FeatureCollection }) { this.data = options.data }
  getSource() { return this.data ? this.source : undefined }
  addLayer(layer: FakeMap['layers'][string]) { this.layers[layer.id] = layer }
  getLayer(id: string) { return this.layers[id] }
  addControl() {}
  setFilter() {}
  easeTo() {}
  remove() {}
}
vi.mock('maplibre-gl', () => ({
  Map: class { constructor(options: FakeMap['options']) { return new FakeMap(options) } },
  NavigationControl: class {}, AttributionControl: class {},
}))
import { IncidentMap } from './IncidentMap'

const incident = (id: string): Incident => ({
  id, externalIds: [], type: 'EARTHQUAKE', title: id, severity: 'HIGH', status: 'ACTIVE',
  location: { longitude: -122, latitude: 38 }, startedAt: '', updatedAt: '', createdAt: '',
  sources: [], metrics: {}, provenance: {},
})
const props = { selectedId: null, region: 'GLOBAL' as const, onSelect: vi.fn(), onPreview: vi.fn(), onClusterPreview: vi.fn() }
beforeEach(() => {
  state.maps.length = 0
  vi.stubGlobal('matchMedia', () => ({ matches: true }))
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

it('initializes layers and the latest GeoJSON before basemap tiles or glyphs finish', () => {
  const view = render(<IncidentMap {...props} incidents={[]} />)
  view.rerender(<IncidentMap {...props} incidents={[incident('latest')]} />)
  const map = state.maps[0]
  act(() => map.fire('style.load'))
  expect(map.options.style).toBe('https://tiles.openfreemap.org/styles/dark')
  expect(map.data?.features[0]).toMatchObject({ geometry: { coordinates: [-122, 38] }, properties: { id: 'latest' } })
  expect(Object.keys(map.layers)).toHaveLength(7)
  expect(map.layers.events.type).toBe('circle')
  expect(map.layers.clusters.type).toBe('circle')
  expect(map.layers['cluster-count'].layout?.['text-font']).toEqual(['Noto Sans Regular'])
  expect(map.layers['event-symbols'].layout?.['text-font']).toEqual(['Noto Sans Regular'])
})

it('updates and clears incidents during tile loading after the one-time load event', () => {
  const view = render(<IncidentMap {...props} incidents={[]} />)
  const map = state.maps[0]
  act(() => { map.fire('style.load'); map.fire('load') })
  view.rerender(<IncidentMap {...props} incidents={[incident('arrived-after-load')]} />)
  expect(map.data?.features).toHaveLength(1)
  view.rerender(<IncidentMap {...props} incidents={[]} />)
  expect(map.data?.features).toHaveLength(0)
  expect(map.source.setData).toHaveBeenCalledTimes(2)
  expect(map.loaded).not.toHaveBeenCalled()
})
