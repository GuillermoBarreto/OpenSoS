# Deployment

## Render

Create a Blueprint from `backend/render.yaml`, or a Python service rooted at `backend`. Build with `pip install -r requirements.txt`; start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `APP_ENV=production`, `CORS_ORIGINS=https://your-app.vercel.app`; health path `/health`.

For optional AI briefs, set `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`, and `AI_TIMEOUT_SECONDS` on Render only. Never expose the key through Vercel. Missing AI settings leave the application operational.

## Vercel

Set root `frontend`, framework Vite, build `npm run build`, output `dist`, and `VITE_API_BASE_URL=https://your-render-service.onrender.com`. `vercel.json` preserves shareable query URLs.

### Basemap and incident rendering

The map uses [OpenFreeMap's Dark style](https://tiles.openfreemap.org/styles/dark).
The [public service explicitly permits keyless use](https://openfreemap.org/),
including commercial use. No tile credential or additional Vercel environment
variable is required. Keep MapLibre's attribution control enabled: the source
TileJSON supplies OpenFreeMap, OpenMapTiles, and OpenStreetMap attribution.
The public service has no SLA. The dark style replaces CARTO raster tiles while
retaining the application's dark overlays and incident colors.

[CARTO now requires a basemap key](https://carto.com/basemaps/apikey/), including
for Dark Matter raster URLs. Its unauthenticated endpoint can return HTTP 200
with an API-key watermark inside the image. Do not restore the old keyless URL.
If CARTO is reintroduced, use a browser-safe basemap key with origin restrictions;
never expose a server API credential through a `VITE_` variable.

Incident sources/layers initialize on `style.load`, before basemap tiles finish.
Data and filter changes update the existing GeoJSON source without waiting for
`map.loaded()` (which can be false after the one-time `load` event). Circle
markers do not require glyphs. Cluster counts and event symbols explicitly use
the style's Noto Sans Regular glyph service. Severe weather and tsunami use
`★` and `≃` throughout the UI because the provider's font lacks `✦` and `≋`.

For release verification, run the production preview and check desktop/mobile
map dimensions, geography, markers, zoom, filters, attribution, and console
errors. Inspect tile contents as well as status codes. Test slow/failed basemap
and glyph requests separately from incident source updates.

Render restarts clear the cache. Before scaling replicas, implement the repository with PostgreSQL/PostGIS or a shared cache.
