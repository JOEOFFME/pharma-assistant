"""Offline voice prerequisite checks; never download model files from a request."""

import importlib.util
import shutil
from pathlib import Path


def check_voice(config: dict) -> dict:
    """Report actionable prerequisite codes without leaking local filesystem paths."""
    issues = []
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            issues.append(f"{tool}_missing")
    if importlib.util.find_spec("faster_whisper") is None:
        issues.append("speech_dependency_missing")
    else:
        try:
            from faster_whisper.utils import download_model

            if Path(config["model"]).is_dir():
                snapshot = Path(config["model"])
            else:
                snapshot = Path(
                    download_model(
                        config["model"],
                        revision=config.get("revision"),
                        local_files_only=True,
                    )
                )
            if not all(
                (snapshot / name).is_file()
                for name in ("model.bin", "config.json", "tokenizer.json")
            ):
                issues.append("model_not_cached")
        except (ImportError, OSError, RuntimeError, ValueError):
            issues.append("model_not_cached")
    return {"ready": not issues, "issues": issues, "model": config["model"]}
