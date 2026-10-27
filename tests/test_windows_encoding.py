"""Exercise first-start directory rebuilding under a Windows-like ANSI default."""

import hashlib
import json
from pathlib import Path

from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.clean_pharmacies import build_directory


def test_arabic_directory_build_ignores_cp1252_default(tmp_path, monkeypatch):
    """Arabic names must round-trip in metrics, CSV and SQLite without UTF8 mode."""
    name = "صيدلية الاختبار"
    payload = json.dumps(
        {
            "osm3s": {"timestamp_osm_base": "2026-01-01T00:00:00Z"},
            "elements": [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 34,
                    "lon": -6,
                    "tags": {
                        "amenity": "pharmacy",
                        "name": name,
                        "addr:city": "الرباط",
                    },
                }
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    (tmp_path / "source.json").write_bytes(payload)
    manifest = {
        "responses": [
            {
                "file": "source.json",
                "region": "الرباط",
                "osm_timestamp": "2026-01-01T00:00:00Z",
                "elements": 1,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ]
    }
    # Report generator expects provenance fields from the normal fetcher.
    manifest.update(
        source="Test-only fixture",
        attribution="Test only",
        license="ODbL-1.0",
        license_url="https://example.invalid/",
        fetched_at="test",
        endpoint="test",
        country="MA",
        scope="test-only",
        requested_regions=["الرباط"],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    original_open = Path.open

    def ansi_open(
        self, mode="r", buffering=-1, encoding=None, errors=None, newline=None
    ):
        if "b" not in mode and encoding is None:
            encoding = "cp1252"
        return original_open(self, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", ansi_open)
    config = {
        "csv_path": str(tmp_path / "directory.csv"),
        "database_path": str(tmp_path / "directory.sqlite3"),
        "metrics_path": str(tmp_path / "metrics.json"),
        "report_path": str(tmp_path / "report.md"),
        "city_aliases": {},
        "dedupe_distance_m": 20,
    }
    metrics = build_directory(manifest_path, config)
    assert json.loads((tmp_path / "metrics.json").read_bytes()) == metrics
    assert "الرباط".encode() in (tmp_path / "metrics.json").read_bytes()
    assert name.encode("utf-8") in (tmp_path / "directory.csv").read_bytes()
    assert PharmacyRepository(tmp_path / "directory.sqlite3").all()[0].name == name
