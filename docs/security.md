# Security and privacy

Provider calls are server-side, identify OpenSoS, follow redirects, and have timeouts. Pydantic validates normalized models; FastAPI validates enums, dates, limits, and bounding boxes. CORS is allow-listed. React renders provider strings as text, never injected HTML.

Milestone 1 has no secrets, accounts, analytics, automatic location, uploads, or community content. Keep `.env` untracked; expose only `VITE_API_BASE_URL` in the browser.
