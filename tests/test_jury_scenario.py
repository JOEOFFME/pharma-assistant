"""Fictional stock/duty examples stay explicit and isolated from real answers."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app
from pharma_assistant.api.jury_scenario import scenario_answer
from pharma_assistant.asr.transcriber import Transcription

SCENARIOS = json.loads(
    (Path(__file__).resolve().parents[1] / "web/assets/jury-scenarios.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("question", SCENARIOS, ids=lambda q: q["id"])
def test_exact_requested_examples_return_concrete_fictional_information(question):
    # Demo text needs no external service, model or production medicine database.
    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/demo/assistant/text",
            json={k: question[k] for k in ("text", "language_hint")},
        )
    assert response.status_code == 200
    result = response.json()
    assert result["synthetic"] is True
    assert result["scenario_kind"] == question["kind"]
    assert "données fictives" in result["answer"]
    assert all(phrase in result["answer"] for phrase in question["answer_contains"])
    assert all(p["synthetic"] for p in result["pharmacies"])
    assert result["actions"] == []
    assert "https://" not in result["answer"] and "+212" not in result["answer"]


def test_nearby_order_and_origin_do_not_claim_users_actual_position():
    result = scenario_answer(SCENARIOS[0]["text"])
    assert [p["distance_m"] for p in result["pharmacies"]] == [350, 800, 1200]
    assert "fictif" in result["origin"]
    assert all(
        "latitude" not in p and "longitude" not in p for p in result["pharmacies"]
    )


@pytest.mark.parametrize(
    "text, kind",
    [
        ("Liste des pharmacies les plus proches", "nearby"),
        ("Panadol disponible à la pharmacie Al Irfane ?", "stock"),
        ("Wach Panadol kayn f Alirfane ?", "stock"),
        ("Où est une pharmacie de garde ce soir ?", "duty"),
        ("أين توجد صيدلية الحراسة؟", "duty"),
        ("فين أقرب صيدلية؟", "nearby"),
        ("واش بانادول كاين فصيدلية العرفان؟", "stock"),
    ],
)
def test_question_variants(text, kind):
    assert scenario_answer(text)["scenario_kind"] == kind


@pytest.mark.parametrize("language", ["fr", "ar", "darija_ar", "darija_latn"])
def test_clinical_questions_still_refused_in_demo(language):
    result = scenario_answer(
        "Quelle dose de Panadol dois je prendre à Al Irfane ?", language
    )
    assert result["scenario_kind"] == "medical_boundary"
    assert not result["pharmacies"]
    assert "12" not in result["answer"]


@pytest.mark.parametrize(
    "text",
    [
        "Wach Panadol kayn f pharmacie inconnue ?",
        "Wach Augmentin kayn f Al Irfane ?",
        "Prix Panadol à Al Irfane ?",
        "Raconte-moi une histoire",
    ],
)
def test_unknown_stock_price_or_pharmacy_is_not_fabricated(text):
    result = scenario_answer(text)
    assert result["scenario_kind"] == "help"
    assert not result["pharmacies"]


def test_real_endpoints_do_not_inherit_fictional_stock_or_duty(pipeline):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        for question in SCENARIOS[1:]:
            real = client.post(
                "/v1/assistant/text",
                json={"text": question["text"], "language_hint": "fr"},
            ).json()
            assert not real.get("synthetic")
            assert "12 boîtes" not in real["answer"]
            assert "Démo Nuit" not in real["answer"]
            if question["id"] == "duty":
                assert "ne peux pas confirmer" in real["answer"]


def test_actual_voice_transcript_is_routed_to_same_explicit_demo(pipeline):
    from test_project_service import wav_bytes

    class FakeASR:
        def transcribe(self, path, language=None):
            return Transcription(SCENARIOS[1]["text"], "fr", 0.25)

    app = create_app()
    app.state.pipeline = pipeline
    app.state.transcriber = FakeASR()
    with TestClient(app) as client:
        response = client.post(
            "/v1/demo/assistant/voice",
            data={"language_hint": "darija_latn"},
            files={"file": ("test.wav", wav_bytes(), "audio/wav")},
        )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["transcript"] == SCENARIOS[1]["text"]
    assert result["synthetic"] and result["scenario_kind"] == "stock"
    assert "12 boîtes" in result["answer"]


def test_demo_routes_preserve_auth_and_validation(monkeypatch):
    with TestClient(create_app()) as client:
        assert (
            client.post("/v1/demo/assistant/text", json={"text": " "}).status_code
            == 422
        )
    monkeypatch.setenv("API_KEY", "test-only-key")
    with TestClient(create_app()) as client:
        assert (
            client.post("/v1/demo/assistant/text", json={"text": "salam"}).status_code
            == 401
        )
        assert client.post("/v1/demo/assistant/voice").status_code == 401
