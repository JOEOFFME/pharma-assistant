"""Mocked OpenRouter contract and local grounding; no paid inference in tests."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from pharma_assistant.api.answers import present_answer
from pharma_assistant.api.app import create_app
from pharma_assistant.nlp.openrouter import (
    ENDPOINT,
    GroundedReply,
    OpenRouterPipeline,
    OpenRouterProvider,
    QueryPlan,
)


def span(text, mention):
    start = text.index(mention)
    return {"text": mention, "start": start, "end": start + len(mention)}


def plan(
    text, *, intent="check_availability", medications=(), pharmacies=(), locations=()
):
    return QueryPlan(
        intent=intent,
        language="darija_latn",
        medical_advice=False,
        medications=[span(text, m) for m in medications],
        pharmacies=[span(text, p) for p in pharmacies],
        locations=[span(text, p) for p in locations],
    )


class Provider:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def plan(self, text):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_exact_darija_stock_request_can_improve_unknown_baseline_intent(pipeline):
    text = "f pharmacy al Irfane wach n9der nl9a endhom Panadol"
    provider = Provider(plan(text, medications=["Panadol"], pharmacies=["al Irfane"]))
    result = OpenRouterPipeline(pipeline, provider).analyze(text)
    assert provider.calls == 1
    assert result.intent.label == "check_availability"
    assert any(e.type == "MEDICATION" and e.text == "Panadol" for e in result.entities)
    answer = present_answer(result)["answer"]
    assert "Panadol" in answer
    assert "stock" in answer
    assert "12" not in answer


@pytest.mark.parametrize(
    "failure", [OSError("offline"), ValueError("invalid JSON"), TimeoutError()]
)
def test_one_failure_falls_back_without_retrying_or_inventing_answer(pipeline, failure):
    provider = Provider(failure)
    text = "Bonjour"
    expected = pipeline.analyze(text)
    result = OpenRouterPipeline(pipeline, provider).analyze(text)
    assert result.intent == expected.intent
    assert provider.calls == 1


def test_invented_source_city_is_rejected(pipeline):
    text = "3tini a9rab pharmacy lya"
    proposed = plan(text, intent="pharmacy_info_location")
    payload = proposed.model_dump()
    payload["locations"] = [{"text": "Casablanca", "start": 0, "end": 10}]
    proposed = QueryPlan.model_validate(payload)
    result = OpenRouterPipeline(pipeline, Provider(proposed)).analyze(text)
    assert not any(e.type == "LOCATION" for e in result.entities)


def test_model_cannot_drop_a_locally_recognized_city(pipeline):
    text = "Adresse de la pharmacie Atlas à Rabat ?"
    proposed = plan(text, intent="pharmacy_info_location", pharmacies=["Atlas"])
    expected = pipeline.analyze(text)
    result = OpenRouterPipeline(pipeline, Provider(proposed)).analyze(text)
    assert result.entities == expected.entities
    assert any(e.type == "LOCATION" and e.text == "Rabat" for e in result.entities)


def test_known_clinical_request_never_calls_provider(pipeline):
    provider = Provider(ValueError("must not be called"))
    result = OpenRouterPipeline(pipeline, provider).analyze(
        "Quelle dose de Doliprane ?"
    )
    assert provider.calls == 0
    assert result.intent.label == "out_of_scope"


def test_model_detected_clinical_intent_uses_fixed_refusal(pipeline):
    text = "Wach had dwa mzyan lya ?"
    proposed = plan(text)
    proposed.medical_advice = True
    result = OpenRouterPipeline(pipeline, Provider(proposed)).analyze(
        text, language_hint="fr"
    )
    assert result.intent.label == "out_of_scope"
    # An unknown clinical phrasing is never answered with an invented recommendation.
    assert "ne peux pas donner de conseil médical" in present_answer(result)["answer"]


def test_model_cannot_reaffirm_locally_negated_medicine(pipeline):
    text = "pas Doliprane mais Spasfon disponible ?"
    proposed = plan(text, medications=["Doliprane", "Spasfon"])
    result = OpenRouterPipeline(pipeline, Provider(proposed)).analyze(text)
    rejected = next(
        e for e in result.entities if e.type == "MEDICATION" and e.text == "Doliprane"
    )
    assert rejected.assertion == "negated"


def test_plan_schema_has_no_factual_answer_fields():
    fields = QueryPlan.model_json_schema()["properties"]
    assert set(fields) == {
        "intent",
        "language",
        "medical_advice",
        "medications",
        "pharmacies",
        "locations",
    }
    with pytest.raises(ValidationError):
        QueryPlan.model_validate({**plan("salam").model_dump(), "stock": 12})


def test_chat_http_contract_keeps_key_out_of_body_and_bounds_response(monkeypatch):
    captured = {}
    expected = plan("salam", intent="greeting_smalltalk")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            assert limit == 131073
            return json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": expected.model_dump_json()},
                        }
                    ]
                }
            ).encode()

    def fake_open(request, timeout):
        captured["request"] = request
        assert timeout == 12
        return Response()

    monkeypatch.setattr("pharma_assistant.nlp.openrouter.urlopen", fake_open)
    provider = OpenRouterProvider("test-secret-only", "author/model")
    assert provider.plan("salam") == expected
    request = captured["request"]
    assert request.full_url == ENDPOINT
    assert request.get_header("Authorization") == "Bearer test-secret-only"
    assert b"test-secret-only" not in request.data
    body = json.loads(request.data)
    assert body["model"] == "author/model"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["provider"]["require_parameters"] is True
    assert body["messages"][-1]["content"] == "salam"


@pytest.mark.parametrize(
    "response",
    [
        b"{}",
        b"not JSON",
        b"x" * 131073,
        b'{"choices":[{"finish_reason":"length","message":{"content":"{}"}}]}',
    ],
)
def test_provider_rejects_error_truncated_invalid_and_oversized_responses(
    monkeypatch, response
):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return response

    monkeypatch.setattr(
        "pharma_assistant.nlp.openrouter.urlopen", lambda *a, **k: Response()
    )
    with pytest.raises(ValueError):
        OpenRouterProvider("test-only", "author/model").plan("salam")


def test_openrouter_is_used_by_consumer_route_only_when_explicitly_enabled(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_NLU", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret-only")
    monkeypatch.setenv("OPENROUTER_MODEL", "author/model")
    text = "f pharmacy al Irfane wach n9der nl9a endhom Panadol"
    calls = []

    def fake_plan(self, value):
        calls.append(value)
        return plan(value, medications=["Panadol"], pharmacies=["al Irfane"])

    monkeypatch.setattr(OpenRouterProvider, "plan", fake_plan)
    monkeypatch.setattr(
        "pharma_assistant.api.data_chat.compose_reply",
        lambda *args, **kwargs: (
            GroundedReply(
                answer="Panadol : stock non confirmé.",
                source_ids=[],
                stock_status="unverified",
                duty_status="unverified",
                medical_refusal=False,
            ),
            "author/model",
        ),
    )
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        response = client.post("/v1/assistant/text", json={"text": text})
        assert response.status_code == 200, response.text
        assert response.json()["analysis"]["intent"]["label"] == "check_availability"
        assert calls == [text]
        html = client.get("/").text
        assert "test-secret-only" not in html
        assert client.get("/version").json()["consumer_nlu"] == "openrouter"


def test_missing_openrouter_settings_are_not_silently_reported_as_connected(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_NLU", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        response = client.post("/v1/assistant/text", json={"text": "salam"})
        assert response.status_code == 200
        assert response.json()["model"] is None
        assert response.json()["fallback_reason"] == "openrouter_key_missing"


@pytest.mark.parametrize("status", [401, 402, 429, 503])
def test_provider_http_errors_fall_back_without_exposing_credentials(
    pipeline, monkeypatch, status
):
    from urllib.error import HTTPError

    def unavailable(*args, **kwargs):
        raise HTTPError(ENDPOINT, status, "provider unavailable", None, None)

    monkeypatch.setattr("pharma_assistant.nlp.openrouter.urlopen", unavailable)
    result = OpenRouterPipeline(
        pipeline, OpenRouterProvider("test-secret-only", "author/model")
    ).analyze("Bonjour", language_hint="fr")
    answer = present_answer(result)["answer"]
    assert "Pharma-AI" in answer
    assert "test-secret-only" not in answer
