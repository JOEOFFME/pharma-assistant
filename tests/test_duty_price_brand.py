"""Reported duty/price requests receive truthful, actionable consumer replies."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.answers import present_answer
from pharma_assistant.api.app import create_app
from pharma_assistant.api.service import Location

ROOT = Path(__file__).resolve().parents[1]
DUTY_PROMPT = "chno howa l pharmacie li fih la garde had lila"


def test_reported_duty_request_is_not_a_fake_pharmacy_name(pipeline):
    analysis = pipeline.analyze(DUTY_PROMPT)
    assert analysis.intent.label == "pharmacy_info_hours"
    assert not any(e.type == "PHARMACY_NAME" for e in analysis.entities)
    assert any(e.type == "TIME_REF" and e.text == "had lila" for e in analysis.entities)
    result = present_answer(analysis)
    assert "ne peux pas confirmer" in result["answer"]
    assert "Je n’ai pas trouvé" not in result["answer"]
    assert "ville" in result["answer"]
    assert result["pharmacies"] == []
    assert {a["type"] for a in result["actions"]} == {"find_pharmacy", "share_location"}


@pytest.mark.parametrize(
    "text",
    [
        "Pharmacie de garde à Rabat ce soir ?",
        "Quelle pharmacie est de garde à Rabat demain ?",
        "صيدلية اللي فيها الحراسة الليلة",
    ],
)
def test_duty_never_promises_live_confirmation_even_with_location(pipeline, text):
    result = present_answer(
        pipeline.analyze(text, language_hint="fr"), Location(latitude=34, longitude=-6)
    )
    assert "ne peux pas confirmer" in result["answer"]
    assert result["pharmacies"] == []
    assert "Je n’ai pas trouvé" not in result["answer"]
    if "Rabat" in text:
        assert result["actions"][0]["city"] == "Rabat"


def test_price_is_one_coherent_answer_not_generic_disambiguation(pipeline):
    result = present_answer(
        pipeline.analyze("Quel est le prix de Doliprane ?", language_hint="fr")
    )
    assert "Doliprane" in result["answer"]
    assert "pas de prix marocain vérifié" in result["answer"]
    assert "Plusieurs présentations" not in result["answer"]
    assert "Pouvez-vous préciser" not in result["answer"]
    assert "pharmacie" in result["answer"]
    assert any(a["type"] == "find_pharmacy" for a in result["actions"])
    assert not any(c.isdigit() for c in result["answer"])


def test_specific_price_request_does_not_repeat_missing_details(pipeline):
    result = present_answer(
        pipeline.analyze("Prix Doliprane 1000 mg en comprimés ?", language_hint="fr")
    )
    assert "pas de prix marocain vérifié" in result["answer"]
    assert "précisez le dosage" not in result["answer"]
    assert "Plusieurs" not in result["answer"]


@pytest.mark.parametrize("language", ["fr", "ar", "darija_ar", "darija_latn"])
def test_brand_greetings_are_consistent(pipeline, language):
    assert (
        "Pharma-AI"
        in present_answer(pipeline.analyze("salam", language_hint=language))["answer"]
    )


def test_consumer_brand_and_exact_endpoint_sequence(pipeline):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        for prompt in [DUTY_PROMPT, "Quel est le prix de Doliprane ?"]:
            response = client.post(
                "/v1/assistant/text", json={"text": prompt, "language_hint": "fr"}
            )
            assert response.status_code == 200, response.text
            assert response.json()["actions"]
        html = client.get("/").text
        script = client.get("/ui/assistant.js").text
        assert "Pharma-AI" in html and "Pharma-AI" in script
        assert "Amine" not in html + script and "أمين" not in html + script
        assert client.get("/openapi.json").json()["info"]["title"] == "Pharma-AI"
