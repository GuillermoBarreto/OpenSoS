import { useEffect, useRef } from 'react'
import maplibregl, { type GeoJSONSource, type Map } from 'maplibre-gl'
import type { FeatureCollection, Point } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'
import { EVENT_VISUALS, type Region } from './eventVisuals'
import type { Incident } from './types'

interface Props { incidents: Incident[]; selectedId: string | null; region: Region; onSelect: (id: string) => void; onPreview: (incident: Incident | null) => void; onClusterPreview: (preview: ClusterPreview | null) => void }
export interface ClusterPreview { total: number; severe: number; breakdown: { label: string; count: number }[] }
const REGIONS: Record<Region, { center: [number, number]; zoom: number }> = { GLOBAL: { center: [5, 20], zoom: 1.35 }, NORTH_AMERICA: { center: [-105, 42], zoom: 2.4 }, SOUTH_AMERICA: { center: [-61, -18], zoom: 2.4 }, EUROPE: { center: [15, 52], zoom: 3.2 }, AFRICA: { center: [20, 2], zoom: 2.5 }, ASIA: { center: [95, 35], zoom: 2.2 }, OCEANIA: { center: [140, -25], zoom: 2.7 } }
const style: maplibregl.StyleSpecification = { version: 8, glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf', sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } }, layers: [{ id: 'osm', type: 'raster', source: 'osm', paint: { 'raster-saturation': -0.82, 'raster-brightness-max': 0.63, 'raster-contrast': 0.3 } }] }

export function IncidentMap({ incidents, selectedId, region, onSelect, onPreview, onClusterPreview }: Props) {
  const container = useRef<HTMLDivElement>(null), mapRef = useRef<Map | null>(null), incidentsRef = useRef(incidents)
  const callbacks = useRef({ onSelect, onPreview, onClusterPreview })
  useEffect(() => { incidentsRef.current = incidents }, [incidents])
  useEffect(() => { callbacks.current = { onSelect, onPreview, onClusterPreview } }, [onSelect, onPreview, onClusterPreview])
  useEffect(() => {
    if (!container.current || mapRef.current) return
    const map = new maplibregl.Map({ container: container.current, style, center: REGIONS.GLOBAL.center, zoom: REGIONS.GLOBAL.zoom, minZoom: 1, maxZoom: 12, attributionControl: false })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-left'); map.addControl(new maplibregl.AttributionControl({ compact: true }))
    map.on('load', () => {
      const clusterProperties: Record<string, maplibregl.ExpressionSpecification> = { severe: ['+', ['case', ['in', ['get', 'severity'], ['literal', ['HIGH', 'CRITICAL']]], 1, 0]] }
      Object.keys(EVENT_VISUALS).forEach(type => { clusterProperties[`count_${type}`] = ['+', ['case', ['==', ['get', 'type'], type], 1, 0]] })
      map.addSource('incidents', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, cluster: true, clusterMaxZoom: 6, clusterRadius: 48, clusterProperties })
      map.addLayer({ id: 'clusters', type: 'circle', source: 'incidents', filter: ['has', 'point_count'], paint: { 'circle-color': ['case', ['>', ['get', 'severe'], 0], '#d99a43', '#58727b'], 'circle-radius': ['interpolate', ['linear'], ['get', 'point_count'], 1, 17, 100, 25, 500, 32], 'circle-stroke-color': '#eaf1f2', 'circle-stroke-width': 2 } })
      map.addLayer({ id: 'cluster-count', type: 'symbol', source: 'incidents', filter: ['has', 'point_count'], layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 12, 'text-font': ['Open Sans Semibold'] }, paint: { 'text-color': '#111a20' } })
      map.addLayer({ id: 'priority-rings', type: 'circle', source: 'incidents', filter: ['all', ['!', ['has', 'point_count']], ['in', ['get', 'severity'], ['literal', ['HIGH', 'CRITICAL']]]], paint: { 'circle-radius': ['match', ['get', 'severity'], 'CRITICAL', 17, 13], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': ['get', 'color'], 'circle-stroke-width': ['match', ['get', 'severity'], 'CRITICAL', 3, 2], 'circle-opacity': .62 } })
      map.addLayer({ id: 'selected-ring', type: 'circle', source: 'incidents', filter: ['==', ['get', 'id'], ''], paint: { 'circle-radius': 20, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 3, 'circle-opacity': .9 } })
      map.addLayer({ id: 'events', type: 'circle', source: 'incidents', filter: ['!', ['has', 'point_count']], paint: { 'circle-radius': ['match', ['get', 'severity'], 'CRITICAL', 11, 'HIGH', 9, 'MODERATE', 7.5, 'LOW', 6.5, 5.5], 'circle-color': ['get', 'color'], 'circle-stroke-color': '#f4f7f8', 'circle-stroke-width': ['match', ['get', 'severity'], 'CRITICAL', 3, 'HIGH', 2.5, 1.5], 'circle-opacity': .92 } })
      map.addLayer({ id: 'event-symbols', type: 'symbol', source: 'incidents', filter: ['!', ['has', 'point_count']], layout: { 'text-field': ['get', 'symbol'], 'text-size': ['match', ['get', 'severity'], 'CRITICAL', 12, 'HIGH', 11, 9], 'text-allow-overlap': true }, paint: { 'text-color': '#10171d' } })
      map.on('click', 'clusters', async event => { const feature = map.queryRenderedFeatures(event.point, { layers: ['clusters'] })[0]; const source = map.getSource('incidents') as GeoJSONSource; const zoom = await source.getClusterExpansionZoom(Number(feature.properties?.cluster_id)); map.easeTo({ center: (feature.geometry as Point).coordinates as [number, number], zoom }) })
      map.on('click', 'events', event => { const id = event.features?.[0]?.properties?.id; if (id) callbacks.current.onSelect(id) })
      map.on('mousemove', 'events', event => { const id = event.features?.[0]?.properties?.id; callbacks.current.onPreview(incidentsRef.current.find(item => item.id === id) || null) })
      map.on('mouseleave', 'events', () => callbacks.current.onPreview(null))
      map.on('mousemove', 'clusters', event => { const props = event.features?.[0]?.properties || {}; const breakdown = Object.entries(EVENT_VISUALS).map(([type, visual]) => ({ label: visual.label, count: Number(props[`count_${type}`] || 0) })).filter(item => item.count).sort((a,b) => b.count-a.count); callbacks.current.onClusterPreview({ total: Number(props.point_count || 0), severe: Number(props.severe || 0), breakdown }) })
      map.on('mouseleave', 'clusters', () => callbacks.current.onClusterPreview(null))
      for (const layer of ['clusters', 'events']) { map.on('mouseenter', layer, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', layer, () => map.getCanvas().style.cursor = '') }
    }); mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])
  useEffect(() => { const collection: FeatureCollection = { type: 'FeatureCollection', features: incidents.map(item => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [item.location.longitude, item.location.latitude] }, properties: { id: item.id, severity: item.severity, type: item.type, color: EVENT_VISUALS[item.type].color, symbol: EVENT_VISUALS[item.type].symbol } })) }; const update = () => { (mapRef.current?.getSource('incidents') as GeoJSONSource | undefined)?.setData(collection) }; if (mapRef.current?.loaded()) update(); else mapRef.current?.once('load', update) }, [incidents])
  useEffect(() => { const map = mapRef.current; if (!map?.getLayer('selected-ring')) return; map.setFilter('selected-ring', ['==', ['get', 'id'], selectedId || '']); const item = incidents.find(i => i.id === selectedId); if (item) map.easeTo({ center: [item.location.longitude, item.location.latitude], zoom: Math.max(map.getZoom(), 4), padding: { right: window.innerWidth > 768 ? 400 : 0, top: 0, bottom: 0, left: 0 } }) }, [selectedId, incidents])
  useEffect(() => { const target = REGIONS[region]; mapRef.current?.easeTo({ center: target.center, zoom: target.zoom, duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 900 }) }, [region])
  useEffect(() => { if (matchMedia('(prefers-reduced-motion: reduce)').matches) return; let outward = true; const timer = window.setInterval(() => { const map = mapRef.current; if (!map?.getLayer('selected-ring')) return; map.setPaintProperty('selected-ring', 'circle-radius', outward ? 25 : 18); map.setPaintProperty('selected-ring', 'circle-opacity', outward ? .25 : .9); outward = !outward }, 900); return () => clearInterval(timer) }, [])
  return <div className="map" ref={container} role="application" tabIndex={0} aria-label={`Interactive global incident map with ${incidents.length} visible events. Use map controls to pan and zoom.`} />
}
