"""API, learned-model, LLM safety and speech contracts without external credentials."""

import io
import json
import math
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app
from pharma_assistant.asr.transcriber import (
    Transcription,
    WhisperTranscriber,
    validate_audio,
)
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import read_jsonl
from pharma_assistant.eval.speech import speech_metrics
from pharma_assistant.nlp.llm import FakeLLM, LLMExtractor
from pharma_assistant.nlp.supervised import SupervisedNLU
from pharma_assistant.pipeline.hybrid import HybridPipeline

ROOT = Path(__file__).resolve().parents[1]


def wav_bytes(duration: float = 0.25) -> bytes:
    """A generated test tone, explicitly not recorded speech or WER evidence."""
    import struct

    output = io.BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(
            b"".join(
                struct.pack("<h", int(1000 * math.sin(i / 20)))
                for i in range(int(16000 * duration))
            )
        )
    return output.getvalue()


@pytest.fixture
def client(pipeline):
    """Run the actual router with a deterministic, small real-source pipeline."""
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as connected:
        yield connected


def test_text_version_demo_and_schema(client) -> None:
    """Text analysis, version and demo are available with safe structured outputs."""
    response = client.post(
        "/v1/analyze/text", json={"text": "Je voudrais Spasfon", "language_hint": "fr"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["input"]["raw_text"] == "Je voudrais Spasfon"
    assert response.json()["disclaimer"]
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert client.get("/version").json()["version"] == "0.2.0"
    assert "Pharma-AI" in client.get("/").text
    assert "/v1/analyze/voice" in client.get("/openapi.json").json()["paths"]


@pytest.mark.parametrize(
    "body",
    [
        {"text": ""},
        {"text": " "},
        {"text": "a" * 10001},
        {"text": "bonjour", "language_hint": "en"},
        {"text": "hello", "extra": "unknown"},
    ],
)
def test_bad_text_inputs_are_typed_errors(client, body: dict) -> None:
    response = client.post("/v1/analyze/text", json=body)
    assert response.status_code == 422 and response.json()["error"]
    assert response.json()["disclaimer"]


def test_api_key_and_rate_limit(pipeline, monkeypatch) -> None:
    """Authentication and rate limits protect analysis while health stays public."""
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert (
            client.post("/v1/analyze/text", json={"text": "salam"}).status_code == 401
        )
        headers = {"X-API-Key": "test-secret"}
        assert (
            client.post(
                "/v1/analyze/text", json={"text": "salam"}, headers=headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/v1/analyze/text", json={"text": "salam"}, headers=headers
            ).status_code
            == 429
        )


def test_voice_and_medication_search(client) -> None:
    """Actual audio decoding with fake ASR tests the full voice-to-schema boundary."""

    class FakeASR:
        def transcribe(self, path):
            return Transcription("Je voudrais Spasfon", "fr", 0.25)

    client.app.state.transcriber = FakeASR()
    response = client.post(
        "/v1/analyze/voice", files={"file": ("test.wav", wav_bytes(), "audio/wav")}
    )
    assert response.status_code == 200, response.text
    assert response.json()["input"]["modality"] == "voice"
    assert response.json()["input"]["transcript"] == "Je voudrais Spasfon"
    assert (
        client.post(
            "/v1/analyze/voice", files={"file": ("bad.wav", b"not audio", "audio/wav")}
        ).status_code
        == 415
    )
    assert (
        client.get("/v1/medications/search", params={"q": "Spasfon"}).status_code == 200
    )
    assert (
        client.get("/v1/pharmacies/nearby", params={"lat": 999, "lon": 0}).status_code
        == 422
    )


def test_audio_validation_and_resampling(tmp_path: Path) -> None:
    """Validate bytes/duration and actually invoke ffmpeg before injected inference."""
    config = load_config(ROOT / "configs/asr.yaml")
    audio = tmp_path / "tone.wav"
    audio.write_bytes(wav_bytes())
    assert validate_audio(audio, config) == pytest.approx(0.25)

    class FakeModel:
        def transcribe(self, path, **kwargs):
            with wave.open(path) as handle:
                assert handle.getframerate() == 16000 and handle.getnchannels() == 1
            return [SimpleNamespace(text=" bonjour ")], SimpleNamespace(language="fr")

    transcript = WhisperTranscriber(config, FakeModel()).transcribe(audio)
    assert transcript.text == "bonjour"
    config["max_duration_s"] = 0.1
    with pytest.raises(ValueError):
        validate_audio(audio, config)
    assert speech_metrics([("a b c", "a c")])["wer"] == pytest.approx(1 / 3)
    with pytest.raises(ValueError):
        speech_metrics([])


def test_llm_invalid_json_evidence_and_medical_fallback(pipeline) -> None:
    """Invalid JSON/rewritten input falls back; clinical routing cannot be replaced."""
    text = "Je voudrais Spasfon"
    valid = pipeline.analyze(text).model_dump_json(by_alias=True)
    assert (
        LLMExtractor(FakeLLM(["bad", valid]), pipeline).analyze(text).input.raw_text
        == text
    )
    bad = json.loads(valid)
    bad["input"]["raw_text"] = "a different message"
    result = LLMExtractor(FakeLLM([json.dumps(bad)]), pipeline).analyze(text)
    assert result.input.raw_text == text
    result = LLMExtractor(FakeLLM([valid]), pipeline).analyze(
        "Quelle dose de Spasfon ?"
    )
    assert result.intent.label == "out_of_scope"


def test_supervised_and_hybrid_use_training_only(pipeline) -> None:
    """Train on development train data, decode spans and retain safety routing."""
    rows = read_jsonl(ROOT / "data/nlu/generated/train.jsonl")
    model = SupervisedNLU(analyzer="word")
    model.fit(rows)
    prediction = model.predict("Je voudrais Doliprane")
    for e in prediction["entities"]:
        assert "Je voudrais Doliprane"[e["start"] : e["end"]] == e["text"]
    hybrid = HybridPipeline(pipeline, model)
    assert hybrid.analyze("Quelle dose de Spasfon ?").intent.label == "out_of_scope"


def test_unexpected_error_does_not_leak_internal_details() -> None:
    """Unexpected service failures still have a safe typed envelope and trace ID."""

    class BrokenPipeline:
        def analyze(self, *args, **kwargs):
            raise RuntimeError("private patient text must never be echoed")

    app = create_app()
    app.state.pipeline = BrokenPipeline()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/v1/analyze/text", json={"text": "salam"})
        assert response.status_code == 500
        assert response.json()["error"]["message"] == "Internal service error"
        assert "patient text" not in response.text
        assert response.json()["request_id"]


def test_bio_decoder_merges_adjacent_subtokens() -> None:
    """A compound strength remains one entity even when punctuation has no spaces."""
    import numpy as np

    model = SupervisedNLU()
    model.intent = SimpleNamespace(
        classes_=np.array(["check_availability"]),
        predict_proba=lambda texts: np.array([[1.0]]),
    )
    model.ner = SimpleNamespace(
        predict=lambda features: [
            "B-MEDICATION",
            "B-DOSAGE",
            "I-DOSAGE",
            "I-DOSAGE",
            "I-DOSAGE",
        ]
    )
    result = model.predict("Doliprane 875/125 mg")
    assert [e["text"] for e in result["entities"]] == ["Doliprane", "875/125 mg"]


def test_llm_cannot_inject_medical_advice_as_clarification(pipeline) -> None:
    """Schema-valid provider text must never become generated dosage advice."""
    text = "Je voudrais Spasfon"
    payload = pipeline.analyze(text).model_dump(mode="json", by_alias=True)
    payload["needs_clarification"] = True
    payload["clarification_question"] = {"fr": "Prenez 1000 mg trois fois par jour."}
    result = LLMExtractor(FakeLLM([json.dumps(payload)]), pipeline).analyze(text)
    assert (
        result.clarification_question.fr
        == "Pouvez-vous préciser le produit ou la demande ?"
    )


@pytest.mark.parametrize(
    "patch", [{"value": 3}, {"unit": "bottle"}, {"value": 2, "unit": "tablet"}]
)
def test_llm_quantity_claims_must_match_source(pipeline, patch: dict) -> None:
    """A provider cannot change the explicitly requested package count or unit."""
    text = "Je voudrais 2 boîtes de Spasfon"
    payload = pipeline.analyze(text).model_dump(mode="json", by_alias=True)
    next(e for e in payload["entities"] if e["type"] == "QUANTITY").update(patch)
    result = LLMExtractor(FakeLLM([json.dumps(payload)]), pipeline).analyze(text)
    quantity = next(e for e in result.entities if e.type == "QUANTITY")
    assert quantity.value == 2 and quantity.unit == "box"
