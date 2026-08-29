# Deployment

## Render

Create a Blueprint from `backend/render.yaml`, or a Python service rooted at `backend`. Build with `pip install -r requirements.txt`; start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `APP_ENV=production`, `CORS_ORIGINS=https://your-app.vercel.app`; health path `/health`.

For optional AI briefs, set `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`, and `AI_TIMEOUT_SECONDS` on Render only. Never expose the key through Vercel. Missing AI settings leave the application operational.

## Vercel

Set root `frontend`, framework Vite, build `npm run build`, output `dist`, and `VITE_API_BASE_URL=https://your-render-service.onrender.com`. `vercel.json` preserves shareable query URLs.

Render restarts clear the cache. Before scaling replicas, implement the repository with PostgreSQL/PostGIS or a shared cache.
