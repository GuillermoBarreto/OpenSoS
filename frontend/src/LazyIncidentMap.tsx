import { lazy, Suspense } from 'react'
import type { ComponentProps } from 'react'
import type { IncidentMap as IncidentMapComponent } from './IncidentMap'

const Map = lazy(() => import('./IncidentMap').then(module => ({ default: module.IncidentMap })))

export function IncidentMap(props: ComponentProps<typeof IncidentMapComponent>) {
  return (
    <Suspense fallback={<div className="map" role="status">Loading interactive map…</div>}>
      <Map {...props} />
    </Suspense>
  )
}
