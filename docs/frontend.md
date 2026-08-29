# Frontend

One viewport-filling MapLibre map uses a clustered GeoJSON source. React controls API state, filters/search, telemetry, and selection; MapLibre renders points so React does not create thousands of marker components. Selection updates `?incident=<id>` and restores after initialization.

Above 768 px the inspector uses the right edge; at and below 768 px it becomes a bounded bottom sheet. The page supports 320 px upward without horizontal page scrolling.
