import asyncio
import json
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.main as main_module
from app.intelligence.models import GeneratedBrief
from app.intelligence.service import IntelligenceError, IntelligenceService, build_context
from app.main import app, repository
from app.models import ProviderName


class FakeProvider:
    name, model = "fake", "test-model"

    def __init__(self, result=None, error=None, delay=0):
        self.result, self.error, self.delay, self.calls, self.context = result, error, delay, 0, None

    async def generate_incident_brief(self, context):
        self.calls += 1
        self.context = context
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.result


def valid_result(sources=None):
    return GeneratedBrief(headline="Earthquake near Japan", summary="A magnitude 6.1 earthquake is reported in Test Region.",
                          keyPoints=["USGS reports magnitude 6.1."], sourcesUsed=sources or ["USGS"])


@pytest.mark.asyncio
async def test_ai_disabled_without_provider(incident_factory):
    with pytest.raises(IntelligenceError, match="not configured") as raised:
        await IntelligenceService(None).generate(incident_factory())
    assert raised.value.code == "AI_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_configured_provider_returns_valid_grounded_brief(incident_factory):
    provider = FakeProvider(valid_result())
    brief = await IntelligenceService(provider).generate(incident_factory())
    assert brief.headline == "Earthquake near Japan" and brief.generated_at.tzinfo is not None
    assert provider.context.incident_id == incident_factory().id


@pytest.mark.asyncio
async def test_timeout_is_safe(incident_factory):
    with pytest.raises(IntelligenceError) as raised:
        await IntelligenceService(FakeProvider(valid_result(), delay=.05), timeout_seconds=.001).generate(incident_factory())
    assert raised.value.code == "AI_TIMEOUT" and raised.value.status_code == 504


@pytest.mark.asyncio
async def test_provider_failure_is_safe(incident_factory):
    with pytest.raises(IntelligenceError) as raised:
        await IntelligenceService(FakeProvider(error=RuntimeError("secret provider detail"))).generate(incident_factory())
    assert raised.value.code == "AI_UNAVAILABLE" and "secret" not in raised.value.message


@pytest.mark.asyncio
async def test_malformed_output_and_pydantic_contract(incident_factory):
    with pytest.raises(ValidationError):
        GeneratedBrief(headline="", summary="ok", keyPoints=[], sourcesUsed=[])
    with pytest.raises(IntelligenceError) as raised:
        await IntelligenceService(FakeProvider({"headline": "Incomplete"})).generate(incident_factory())
    assert raised.value.code == "AI_INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_cache_hit_and_invalidation(incident_factory):
    incident = incident_factory(); provider = FakeProvider(valid_result()); service = IntelligenceService(provider)
    first = await service.generate(incident); second = await service.generate(incident)
    assert provider.calls == 1 and not first.cached and second.cached
    incident.updated_at += timedelta(minutes=1)
    assert not (await service.generate(incident)).cached and provider.calls == 2


@pytest.mark.asyncio
async def test_rejects_source_not_attached_to_incident(incident_factory):
    with pytest.raises(IntelligenceError) as raised:
        await IntelligenceService(FakeProvider(valid_result(["GDACS"]))).generate(incident_factory())
    assert raised.value.code == "AI_INVALID_RESPONSE"


def test_grounding_context_contains_normalized_facts_only(incident_factory):
    context = build_context(incident_factory())
    assert context.sources == ["USGS"] and context.metrics == {"magnitude": 6.1}
    assert context.provider_facts[0].external_id == "one"
    assert not hasattr(context, "provenance") and context.updated_at.tzinfo is not None


def test_status_not_found_and_safe_api_errors(incident_factory, monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(main_module, "intelligence_service", IntelligenceService(None))
    status = client.get("/api/intelligence/status").json()
    assert status == {"available": False, "configured": False, "provider": None, "model": None}
    assert "key" not in json.dumps(status).lower()
    missing = client.post("/api/intelligence/incidents/missing/brief")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "INCIDENT_NOT_FOUND"
    item = incident_factory(); repository.replace_provider(ProviderName.USGS, [item])
    disabled = client.post(f"/api/intelligence/incidents/{item.id}/brief")
    assert disabled.status_code == 503 and disabled.json()["error"]["code"] == "AI_NOT_CONFIGURED"


def test_valid_brief_endpoint(incident_factory, monkeypatch):
    item = incident_factory(); repository.replace_provider(ProviderName.USGS, [item])
    monkeypatch.setattr(main_module, "intelligence_service", IntelligenceService(FakeProvider(valid_result())))
    response = TestClient(app).post(f"/api/intelligence/incidents/{item.id}/brief")
    assert response.status_code == 200
    assert response.json()["sourcesUsed"] == ["USGS"]


def test_evaluation_fixtures_define_grounded_expectations():
    fixtures = json.loads((Path(__file__).parent / "fixtures" / "ai_incidents.json").read_text())
    assert fixtures["earthquake"]["required"] == ["earthquake", "6.3", "Japan"]
    assert "acres" in fixtures["wildfire"]["prohibited"]
    assert fixtures["cyclone"]["metrics"]["alertLevel"] == "Orange"
