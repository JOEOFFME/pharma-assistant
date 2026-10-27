"""Shared real-source baseline fixture; no network or gold-file access."""

import copy
from pathlib import Path

import pytest

from pharma_assistant.data.medications import MedicationRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.ingest_medications import build_medications
from pharma_assistant.matching.medications import MedicationIndex
from pharma_assistant.pipeline.text_pipeline import TextPipeline

ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config(ROOT / "configs/baseline.yaml")


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory: pytest.TempPathFactory) -> TextPipeline:
    """Build a small real-source catalogue independently of draft/gold annotations."""
    med_config = load_config(ROOT / "configs/medications.yaml")
    med_config["snapshot_dir"] = str(ROOT / med_config["snapshot_dir"])
    directory = tmp_path_factory.mktemp("baseline_medications")
    med_config.update(
        database_path=str(directory / "medications.sqlite3"),
        metrics_path=str(directory / "metrics.json"),
        results_path=str(directory / "results.json"),
        report_path=str(directory / "report.md"),
        queries_path=str(ROOT / med_config["queries_path"]),
    )
    build_medications(med_config)
    records = MedicationRepository(Path(med_config["database_path"])).all()
    chosen = []
    for record in records:
        if record.brand_name in {"DOLIPRANE", "SPASFON", "AUGMENTIN"}:
            if record.brand_name not in {r.brand_name for r in chosen}:
                chosen.append(record)
    index = MedicationIndex(chosen, med_config["matching"])
    config = copy.deepcopy(CONFIG)
    config["lexicon_seed"] = str(ROOT / config["lexicon_seed"])
    return TextPipeline(config, index, {"Rabat": "Rabat", "الرباط": "Rabat"})


@pytest.fixture(autouse=True)
def offline_consumer_default(monkeypatch):
    """Tests never inherit an operator's opt-in paid consumer provider setting."""
    monkeypatch.setenv("ASSISTANT_NLU", "baseline")
