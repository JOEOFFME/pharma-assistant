"""The curated demonstration uses normal analysis and truthful source-backed replies."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app

QUESTIONS = json.loads(
    (Path(__file__).resolve().parents[1] / "web/assets/demo-questions.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("question", QUESTIONS, ids=lambda question: question["id"])
def test_jury_question_through_consumer_endpoint(pipeline, question):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        response = client.post(
            "/v1/assistant/text",
            json={key: question[key] for key in ("text", "language_hint")},
        )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["analysis"]["intent"]["label"] == question["intent"]
    for phrase in question["answer_contains"]:
        assert phrase in result["answer"]
    if question["id"] == "city":
        assert result["pharmacies"]
        assert all(p["city"] == "Rabat" for p in result["pharmacies"])
    if question["id"] == "phone":
        assert len(result["pharmacies"]) == 1
        assert "+212537675669" in result["pharmacies"][0]["phones_e164"]
    if question["id"] == "request":
        assert "Pouvez-vous préciser" not in result["answer"]
    if question["id"] == "duty":
        assert not result["pharmacies"]
    if question["id"] in {"nearby", "price", "duty"}:
        assert any(a["type"] == "find_pharmacy" for a in result["actions"])


def test_summary_does_not_assign_one_medicines_strength_to_another(pipeline):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        result = client.post(
            "/v1/assistant/text",
            json={
                "text": "Je voudrais Doliprane 1000 mg et Spasfon",
                "language_hint": "fr",
            },
        ).json()
    assert "Doliprane" in result["answer"] and "Spasfon" in result["answer"]
    assert "Spasfon » — 1000 mg" not in result["answer"]
