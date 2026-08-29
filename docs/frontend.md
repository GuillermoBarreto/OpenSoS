# Frontend

One viewport-filling MapLibre map uses a clustered GeoJSON source. React controls API state, filters/search, telemetry, and selection; MapLibre renders points so React does not create thousands of marker components. Selection updates `?incident=<id>` and restores after initialization.

Above 768 px the inspector uses the right edge; at and below 768 px it becomes a bounded bottom sheet. The page supports 320 px upward without horizontal page scrolling.

## Visual and interaction system

Incident type supplies color and a non-color symbol; severity independently supplies size, stroke, and an outer priority ring. MapLibre cluster properties aggregate type and high/critical counts in the rendering worker. Hovering events or clusters displays one concise React preview rather than creating marker elements. Selected-event ring animation is paint-property based, limited to one feature, and disabled for reduced-motion users.

Filters use loaded-data counts and cover type, severity, provider, and updated-time windows (hour, 6 hours, 24 hours, 7 days, all active). Region navigation changes only camera center/zoom and preserves filters. Provider controls expose sanitized status, cache age, incident count, and official links.

The initial request anticipates Render sleep: the UI reports a waking state and retries with bounded backoff before showing a persistent error. Deep-linked selection remains independent of filters and camera navigation.
