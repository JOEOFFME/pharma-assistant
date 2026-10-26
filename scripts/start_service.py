"""Prepare attributed offline reference data, then serve the local demo/API."""

import os
from pathlib import Path


def main() -> None:
    """Never fetch model weights or public source data during service startup."""
    import uvicorn

    from pharma_assistant.data_tools.clean_pharmacies import build_directory
    from pharma_assistant.data_tools.fetch_pharmacies import load_config
    from pharma_assistant.data_tools.ingest_medications import build_medications

    if not Path("data/medications/medications.sqlite3").exists():
        build_medications(load_config(Path("configs/medications.yaml")))
    if not Path("data/pharmacies/pharmacies.sqlite3").exists():
        config = load_config(Path("configs/pharmacies.yaml"))
        build_directory(Path(config["output_dir"]) / "manifest.json", config)
    uvicorn.run(
        "pharma_assistant.api.app:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        access_log=False,
    )


if __name__ == "__main__":
    main()
