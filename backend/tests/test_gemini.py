import asyncio
import json
from types import SimpleNamespace
import pytest
from app.services.gemini_service import GeminiService
from app.core.middleware import QuotaService


def run_assessment(settings, response=None, error=None):
    settings.gemini_enabled = True
    settings.gemini_model = "configured-test-model"
    quotas = QuotaService(settings)
    service = GeminiService(settings, quotas)
    calls = []

    async def generate_content(**kwargs):
        calls.append(kwargs)
        if error:
            raise error
        return response

    service.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    result = asyncio.run(service.assess(b"safe-resized-jpeg"))
    return result, calls


def candidate(text, reason="STOP"):
    return SimpleNamespace(candidates=[SimpleNamespace(finish_reason=reason)], text=text)


def test_disabled_requires_no_key_or_network(settings):
    result = asyncio.run(GeminiService(settings, QuotaService(settings)).assess(b"image"))
    assert result.status == "disabled"


def test_schema_success_without_invented_confidence(settings):
    text = json.dumps({"contains_leaf": "yes", "plant_hypothesis": None, "image_quality": "uncertain",
                       "visible_symptoms": [], "condition_hypothesis": None, "limitations": ["One image only"]})
    result, calls = run_assessment(settings, response=candidate(text))
    assert result.status == "success" and result.assessment.plant_hypothesis is None
    assert "confidence" not in result.assessment.model_dump()
    assert len(calls) == 1


@pytest.mark.parametrize("text", ["", "not json", "{}", '{"contains_leaf":"yes","image_quality":"usable","visible_symptoms":["<script>"]}'])
def test_malformed_or_unsafe_json(settings, text):
    result, _ = run_assessment(settings, response=candidate(text))
    assert result.status == "invalid_response"


def test_refusal(settings):
    result, _ = run_assessment(settings, response=candidate(None, "SAFETY"))
    assert result.status == "refused"


@pytest.mark.parametrize("code,status,count", [(401, "authentication_error", 1), (403, "authentication_error", 1),
                                               (429, "quota_exceeded", 2), (503, "unavailable", 2)])
def test_error_retry_policy(settings, code, status, count):
    error = RuntimeError("safe test error")
    error.code = code
    result, calls = run_assessment(settings, error=error)
    assert result.status == status
    assert len(calls) == count


def test_timeout(settings):
    settings.gemini_enabled = True
    settings.gemini_timeout_seconds = 0.01
    service = GeminiService(settings, QuotaService(settings))

    async def wait(**kwargs):
        await asyncio.sleep(1)

    service.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=wait)))
    assert asyncio.run(service.assess(b"image")).status == "timeout"


def test_network_failure_is_isolated(settings):
    result, calls = run_assessment(settings, error=ConnectionError("offline"))
    assert result.status == "unavailable" and len(calls) == 2
