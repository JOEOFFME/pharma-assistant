"""Human-facing answers preserve uncertainty and the structured API contract."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.answers import present_answer
from pharma_assistant.api.app import create_app
from pharma_assistant.asr.transcriber import Transcription
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.clean_pharmacies import record_from_element


@pytest.mark.parametrize("language", ["fr", "ar", "darija_ar", "darija_latn", "mixed"])
def test_human_answers_for_all_varieties(pipeline, language):
    analysis = pipeline.analyze("Wach kayn dolipran", language_hint=language)
    result = present_answer(analysis)
    assert result["answer"] and "dolipran" in result["answer"]
    assert result["language"] == language
    assert result["analysis"]["input"]["raw_text"] == "Wach kayn dolipran"
    assert result["transcript"] is None
    assert "request_id" not in result["answer"]


def test_stock_order_price_and_medical_uncertainty(pipeline):
    result = present_answer(
        pipeline.analyze("Doliprane disponible ?", language_hint="fr")
    )
    assert "ne dispose pas du stock" in result["answer"]
    result = present_answer(pipeline.analyze("Je voudrais Spasfon", language_hint="fr"))
    assert "Aucune commande" in result["answer"]
    result = present_answer(
        pipeline.analyze("Quel est le prix de Spasfon ?", language_hint="fr")
    )
    assert "pas de prix marocain vérifié" in result["answer"]
    result = present_answer(
        pipeline.analyze("Quelle dose de Spasfon ?", language_hint="fr")
    )
    assert "ne peux pas donner de conseil médical" in result["answer"]
    assert "Prenez" not in result["answer"]


def test_mixed_request_only_echoes_medication(pipeline):
    analysis = pipeline.analyze("Doliprane disponible ?", language_hint="fr")
    analysis.contains_out_of_scope_request = True
    answer = present_answer(analysis)["answer"]
    assert "ne dispose pas du stock" in answer
    assert "ne peux pas donner de conseil médical" in answer


def test_missing_medication_and_location_are_actionable(pipeline):
    assert (
        "Quel médicament"
        in present_answer(pipeline.analyze("Disponible ?", language_hint="fr"))[
            "answer"
        ]
    )
    result = present_answer(
        pipeline.analyze("Où est la pharmacie la plus proche ?", language_hint="fr")
    )
    assert "carte" in result["answer"]


def test_directory_answers_use_real_record_fields_only(pipeline, tmp_path, monkeypatch):
    config_root = Path(__file__).resolve().parents[1] / "configs"
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/pharmacies.yaml").write_bytes(
        (config_root / "pharmacies.yaml").read_bytes()
    )
    monkeypatch.chdir(tmp_path)
    record = record_from_element(
        {
            "type": "node",
            "id": 1,
            "lat": 34,
            "lon": -6,
            "tags": {
                "amenity": "pharmacy",
                "name": "Fixture only",
                "addr:city": "Rabat",
            },
        },
        "test-only",
        {},
    )
    PharmacyRepository(Path("data/pharmacies/pharmacies.sqlite3")).replace_all([record])
    result = present_answer(
        pipeline.analyze("Adresse de la pharmacie à Rabat ?", language_hint="fr")
    )
    assert "Fixture only" in result["answer"]
    assert "Téléphone: inconnu" in result["answer"]
    assert "garde n’est pas vérifiée" in result["answer"]


def test_assistant_endpoint_and_optional_json(pipeline):
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        response = client.post(
            "/v1/assistant/text", json={"text": "Wach kayn dolipran"}
        )
        assert response.status_code == 200
        assert response.json()["answer"]
        assert response.json()["analysis"]["intent"]["label"] == "check_availability"
        # Existing machine-consumer endpoint remains unchanged.
        assert (
            "answer"
            not in client.post("/v1/analyze/text", json={"text": "salam"}).json()
        )
        html = client.get("/").text
        assert '<details id="technical">' in html
        assert '<section id="answer-card" hidden' in html


def test_voice_prerequisites_and_hint_passthrough(pipeline, monkeypatch):
    from test_project_service import wav_bytes

    from pharma_assistant.asr import readiness

    monkeypatch.setattr(readiness.shutil, "which", lambda tool: None)
    monkeypatch.setattr(readiness.importlib.util, "find_spec", lambda name: None)
    app = create_app()
    app.state.pipeline = pipeline
    called = []

    class FakeASR:
        def transcribe(self, path, language=None):
            # Reopen bytes as an external decoder would, after the writer closed.
            assert path.read_bytes().startswith(b"RIFF")
            called.append((path, language))
            return Transcription("Je voudrais Spasfon", "fr", 0.25)

    app.state.transcriber = FakeASR()
    with TestClient(app) as client:
        status = client.get("/v1/voice/status").json()
        assert not status["ready"]
        assert set(status["issues"]) == {
            "ffmpeg_missing",
            "ffprobe_missing",
            "speech_dependency_missing",
        }
        response = client.post(
            "/v1/assistant/voice",
            data={"language_hint": "fr"},
            files={"file": ("test.wav", wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 200, response.text
        assert response.json()["answer"]
        assert response.json()["transcript"] == "Je voudrais Spasfon"
        assert called[0][1] == "fr"
        assert not called[0][0].exists()  # Upload cleaned after inference.
