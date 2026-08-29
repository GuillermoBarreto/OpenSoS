# Security and privacy

AI credentials remain backend-only. Incident prompts contain bounded structured data, delimit provider-controlled text as untrusted, prohibit following embedded instructions, and have no browsing or tool access. Returned source names are checked against incident provenance and user-facing failures omit provider details.

Provider calls are server-side, identify OpenSoS, follow redirects, and have timeouts. Pydantic validates normalized models; FastAPI validates enums, dates, limits, and bounding boxes. CORS is allow-listed. React renders provider strings as text, never injected HTML.

Milestone 1 has no secrets, accounts, analytics, automatic location, uploads, or community content. Keep `.env` untracked; expose only `VITE_API_BASE_URL` in the browser.
