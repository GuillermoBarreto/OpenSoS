# Grounded incident briefs

Milestone 1.5B adds an optional, manually generated AI brief for one selected incident. React calls FastAPI; FastAPI builds a bounded `IncidentBriefContext`; `IntelligenceService` calls an `AIProvider`; and the provider returns a Pydantic-validated structured result. The initial adapter uses OpenAI's Responses API, but incident logic depends only on the provider interface.

Only normalized incident fields, scalar metrics, and attached source records are sent. Raw provider payloads, other incidents, internet retrieval, browsing, and tool calling are excluded. Provider text is delimited as untrusted data and cannot be treated as instructions. The prompt prohibits invented facts, predictions, casualty or damage estimates, panic language, medical advice, and evacuation or emergency recommendations.

Responses contain a headline (120 characters maximum), concise summary, at most five key points, attached source names, and a server-generated UTC timestamp. Post-validation rejects source names not attached to the incident. Failures use safe codes (`AI_NOT_CONFIGURED`, `AI_UNAVAILABLE`, `AI_TIMEOUT`, `AI_INVALID_RESPONSE`, and `INCIDENT_NOT_FOUND`) while technical detail remains in backend logs.

Briefs are cached in memory by incident ID, incident `updatedAt`, and model. A changed incident generates a new brief. Cache state is lost on Render restart and is not shared across replicas. Generation is manual and has no automatic retry.

Configure only the backend/Render service:

```env
AI_PROVIDER=openai
AI_MODEL=gpt-4.1-mini
AI_API_KEY=
AI_TIMEOUT_SECONDS=20
```

With a missing key or provider, OpenSoS starts normally and the inspector reports that briefs are unavailable. Never place `AI_API_KEY` in Vercel or a `VITE_` variable.

AI briefs summarize current OpenSoS data and are not an emergency service or independent authority. They may be incomplete; critical information should be verified with official sources.
