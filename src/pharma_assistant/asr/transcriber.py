"""Bounded audio validation and optional faster-whisper inference."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Transcription:
    """ASR evidence, separate from downstream interpretation."""

    text: str
    language: str | None
    duration_s: float


def validate_audio(path: Path, config: dict) -> float:
    """Check actual decoded streams and duration; extensions do not establish type."""
    if not path.is_file() or not 0 < path.stat().st_size <= config["max_bytes"]:
        raise ValueError("Audio is empty, absent or too large")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of",
                "json",
                str(path.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        if (
            not any(s["codec_type"] == "audio" for s in data["streams"])
            or not 0 < duration <= config["max_duration_s"]
        ):
            raise ValueError("Unsupported stream or audio duration")
        return duration
    except (
        subprocess.SubprocessError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError("Cannot decode audio") from error


class WhisperTranscriber:
    """Load locally cached weights explicitly; inference never silently downloads."""

    def __init__(self, config: dict, model=None) -> None:
        self.config = config
        if model is None:
            from faster_whisper import WhisperModel

            model = WhisperModel(
                config["model"],
                device=config["device"],
                compute_type=config["compute_type"],
                local_files_only=config["local_files_only"],
                revision=config.get("revision"),
            )
        self.model = model

    def transcribe(self, path: Path, language: str | None = None) -> Transcription:
        """Validate, downmix/resample with ffmpeg and return the model transcript."""
        if language not in {None, "ar", "fr"}:
            raise ValueError("ASR language hint must be ar, fr or absent")
        duration = validate_audio(path, self.config)
        with tempfile.TemporaryDirectory(prefix="pharma_asr_") as directory:
            wav = Path(directory) / "audio.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-nostdin",
                    "-i",
                    str(path.resolve()),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(wav),
                ],
                capture_output=True,
                timeout=20,
                check=True,
            )
            segments, info = self.model.transcribe(
                str(wav),
                language=language,
                beam_size=self.config["beam_size"],
                vad_filter=self.config["vad_filter"],
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
        if not text:
            raise ValueError("No intelligible speech detected")
        return Transcription(text, getattr(info, "language", None), duration)
