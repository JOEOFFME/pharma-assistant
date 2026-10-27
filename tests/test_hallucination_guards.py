"""Reject mismatched demo facts and keep speech evidence out of automatic answers."""

import pytest
import yaml
from fastapi.testclient import TestClient

from pharma_assistant.api.answers import present_answer
from pharma_assistant.api.app import create_app
from pharma_assistant.api.jury_scenario import scenario_answer
from pharma_assistant.asr.transcriber import Transcription
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.clean_pharmacies import record_from_element


@pytest.mark.parametrize(
    "text",
    [
        "Panadol al Irfane est périmé ?",
        "Panadol à Al Irfane provoque des effets secondaires ?",
        "Panadol disponible à Al Irfane à Casablanca ?",
        "Panadol et Augmentin disponibles à Al Irfane ?",
        "Panadol disponible à Al Irfane demain ?",
        "La pharmacie Al Irfane est-elle de garde ?",
        "Pharmacie de garde à Tanger demain ?",
        "Quelle pharmacie de garde le 12 novembre ?",
        "Les pharmacies les plus proches de Casablanca",
        "3tini a9rab pharmacy f Tanger",
        "Ne donne pas la liste des pharmacies les plus proches",
        "Panadol pas disponible à Al Irfane ?",
    ],
)
def test_demo_does_not_ignore_changed_meaning_location_medicine_or_date(text):
    result = scenario_answer(text)
    assert result["scenario_kind"] == "help"
    assert result["matched_question"] is False
    assert result["pharmacies"] == []
    assert "12 boîtes" not in result["answer"]
    assert "20:00" not in result["answer"]


def test_consumer_answers_do_not_use_configured_llm_track(pipeline, monkeypatch):
    class UntrustedTrack:
        def analyze(self, *args, **kwargs):
            raise AssertionError("Consumer chat must never call the research track")

    monkeypatch.setenv("NLU_TRACK", "llm")
    app = create_app()
    app.state.pipeline = UntrustedTrack()
    monkeypatch.setattr(
        "pharma_assistant.api.service.TextPipeline.from_config", lambda: pipeline
    )
    with TestClient(app) as client:
        result = client.post("/v1/assistant/text", json={"text": "Bonjour"})
    assert result.status_code == 200
    assert "Pharma-AI" in result.json()["answer"]


def test_named_pharmacy_must_also_match_the_requested_city(
    pipeline, tmp_path, monkeypatch
):
    records = [
        record_from_element(
            {
                "type": "node",
                "id": identifier,
                "lat": 34,
                "lon": -6,
                "tags": {"amenity": "pharmacy", "name": "Atlas", "addr:city": city},
            },
            "test-only",
            {},
        )
        for identifier, city in [(1, "Casablanca"), (2, "Rabat")]
    ]
    database = tmp_path / "directory.sqlite3"
    PharmacyRepository(database).replace_all(records)
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/pharmacies.yaml").write_text(
        yaml.safe_dump(
            {"database_path": str(database), "city_aliases": {"Rabat": "Rabat"}}
        ),
        encoding="utf-8",
    )
    analysis = pipeline.analyze(
        "Téléphone de la pharmacie Atlas à Rabat ?", language_hint="fr"
    )
    monkeypatch.chdir(tmp_path)
    result = present_answer(analysis)
    assert result["pharmacies"]
    assert all(record["city"] == "Rabat" for record in result["pharmacies"])
    assert "Casablanca" not in result["answer"]


def test_transcription_has_no_answer_and_never_calls_a_language_model():
    from test_project_service import wav_bytes

    class FakeASR:
        def transcribe(self, path, language=None):
            return Transcription("Benjure, j'ai vraie de l'apprain.", "fr", 0.25)

    class NoAnalysis:
        def analyze(self, *args, **kwargs):
            raise AssertionError("Unconfirmed speech cannot generate an answer")

    app = create_app()
    app.state.transcriber = FakeASR()
    app.state.pipeline = NoAnalysis()
    with TestClient(app) as client:
        response = client.post(
            "/v1/transcribe/voice",
            data={"language_hint": "fr"},
            files={"file": ("test.wav", wav_bytes(), "audio/wav")},
        )
    assert response.status_code == 200
    assert response.json() == {
        "transcript": "Benjure, j'ai vraie de l'apprain.",
        "requires_confirmation": True,
    }
