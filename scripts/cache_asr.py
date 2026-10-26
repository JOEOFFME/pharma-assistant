"""Explicitly cache the pinned ASR model; serving/inference stays offline."""

from pathlib import Path

from pharma_assistant.data_tools.fetch_pharmacies import load_config


def main() -> None:
    """Run only when downloading public MIT-licensed Whisper weights is intended."""
    from faster_whisper import WhisperModel

    config = load_config(Path("configs/asr.yaml"))
    WhisperModel(
        config["model"],
        device=config["device"],
        compute_type=config["compute_type"],
        revision=config["revision"],
        local_files_only=False,
    )
    print("Pinned ASR weights cached; local_files_only remains enabled for serving.")


if __name__ == "__main__":
    main()
