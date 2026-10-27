"""Reported Darija requests lead to location help instead of medical refusals."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.answers import present_answer
from pharma_assistant.api.app import create_app
from pharma_assistant.api.service import Location
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.clean_pharmacies import record_from_element
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.nlp.intent import classify_intent

ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config(ROOT / "configs/baseline.yaml")


@pytest.mark.parametrize(
    "text",
    [
        "3tini a9rab pharmacy lya",
        "3tini aqrab pharmacie liya",
        "pharmacy 9riba",
        "pharmacie 9rib lia",
        "nearest pharmacy",
        "عطيني أقرب صيدلية",
        "La pharmacie la plus proche ?",
    ],
)
def test_nearest_pharmacy_variants_are_location_requests(text):
    assert classify_intent(text, CONFIG)[:2] == ("pharmacy_info_location", False)


def test_proximity_without_pharmacy_is_not_assumed_to_be_in_scope():
    assert classify_intent("3tini a9rab restaurant lya", CONFIG)[0] == "out_of_scope"


def test_reported_prompt_requests_consent_without_inventing_a_location(pipeline):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        first = client.post("/v1/assistant/text", json={"text": "wach kayn dolipran"})
        assert first.status_code == 200
        assert first.json()["analysis"]["intent"]["label"] == "check_availability"
        response = client.post(
            "/v1/assistant/text", json={"text": "3tini a9rab pharmacy lya"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["analysis"]["intent"]["label"] == "pharmacy_info_location"
        assert data["language"] == "darija_latn"
        assert "diagnostic" not in data["answer"]
        assert data["pharmacies"] == []
        assert [a["type"] for a in data["actions"]] == [
            "find_pharmacy",
            "share_location",
        ]
        assert data["analysis"]["input"]["raw_text"] == "3tini a9rab pharmacy lya"


def test_unknown_request_gets_help_and_medical_advice_still_gets_refused(pipeline):
    unknown = present_answer(pipeline.analyze("xyz blabla", language_hint="fr"))
    assert "Je n’ai pas compris" in unknown["answer"]
    assert "diagnostic" not in unknown["answer"]
    clinical = present_answer(
        pipeline.analyze("Quelle dose de Doliprane ?", language_hint="fr")
    )
    assert "conseil médical" in clinical["answer"]
    mixed = present_answer(
        pipeline.analyze(
            "3tini a9rab pharmacy lya o ch7al nakhod", language_hint="darija_latn"
        )
    )
    assert mixed["analysis"]["intent"]["label"] == "pharmacy_info_location"
    assert mixed["analysis"]["contains_out_of_scope_request"] is True
    assert "diagnostic" in mixed["answer"]
    assert any(a["type"] == "share_location" for a in mixed["actions"])


def test_shared_location_returns_only_nearby_fixture_records(
    pipeline, tmp_path, monkeypatch
):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/pharmacies.yaml").write_bytes(
        (ROOT / "configs/pharmacies.yaml").read_bytes()
    )
    monkeypatch.chdir(tmp_path)
    rows = []
    for identifier, lat in [(1, 34.001), (2, 34.002), (3, 35.0)]:
        rows.append(
            record_from_element(
                {
                    "type": "node",
                    "id": identifier,
                    "lat": lat,
                    "lon": -6,
                    "tags": {
                        "amenity": "pharmacy",
                        "name": f"Test fixture {identifier}",
                    },
                },
                "test only",
                {},
            )
        )
    PharmacyRepository(Path("data/pharmacies/pharmacies.sqlite3")).replace_all(rows)
    analysis = pipeline.analyze("3tini a9rab pharmacy lya")
    result = present_answer(analysis, Location(latitude=34, longitude=-6))
    assert [p["id"] for p in result["pharmacies"]] == ["node/1", "node/2"]
    assert "Test fixture 3" not in result["answer"]
    assert "0.11 km" in result["answer"]
    assert "0.22 km" in result["answer"]
    assert all(p["is_on_duty"] is None for p in result["pharmacies"])
    assert "share_location" not in [a["type"] for a in result["actions"]]
