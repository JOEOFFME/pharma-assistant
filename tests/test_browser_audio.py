"""Decode real streaming WebM bytes like browser MediaRecorder output."""

import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app
from pharma_assistant.asr.transcriber import validate_audio
from pharma_assistant.data_tools.fetch_pharmacies import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_webm_without_duration_metadata(tmp_path):
    # Pipe output deliberately creates non-seekable WebM with no duration tag.
    stream = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.3",
            "-c:a",
            "libopus",
            "-f",
            "webm",
            "pipe:1",
        ],
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout
    audio = tmp_path / "browser.audio"
    audio.write_bytes(stream)
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio),
        ],
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert "duration" not in json.loads(probe.stdout).get("format", {})
    config = load_config(ROOT / "configs/asr.yaml")
    assert validate_audio(audio, config) == pytest.approx(0.3, abs=0.03)
    config["max_duration_s"] = 0.1
    with pytest.raises(ValueError, match="duration"):
        validate_audio(audio, config)


def test_missing_decoder_returns_actionable_503(monkeypatch):
    from test_project_service import wav_bytes

    from pharma_assistant.asr import transcriber

    def missing(*args, **kwargs):
        raise FileNotFoundError("test-only missing ffprobe")

    monkeypatch.setattr(transcriber.subprocess, "run", missing)
    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/assistant/voice", files={"file": ("test.wav", wav_bytes())}
        )
        assert response.status_code == 503
        assert "ffmpeg and ffprobe" in response.json()["error"]["message"]
