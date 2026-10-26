"""Synthetic unit fixtures and offline checks against the saved real OSM snapshot."""

import hashlib
import io
import json
import math
import sqlite3
import urllib.error
from pathlib import Path

import phonenumbers
import pytest

from pharma_assistant.data.pharmacies import PharmacyRepository, haversine_km
from pharma_assistant.data_tools import fetch_pharmacies as fetch
from pharma_assistant.data_tools.clean_pharmacies import (
    build_directory,
    clean_elements,
    coverage_metrics,
    record_from_element,
    write_report,
)
from pharma_assistant.data_tools.pharmacy_normalize import (
    normalize_city,
    normalize_name,
    normalize_phones,
)

ROOT = Path(__file__).resolve().parents[1]
CENTERS = {
    "Rabat": (34.0209, -6.8416),
    "Casablanca": (33.5731, -7.5898),
    "Marrakech": (31.6295, -7.9811),
}


@pytest.fixture
def config() -> dict:
    """Load checked configuration; network tests mock every HTTP call."""
    return fetch.load_config(ROOT / "configs/pharmacies.yaml")


def element(identifier: int = 1, **tags: str) -> dict:
    """Invented test-only OSM-shaped record, never included in production data."""
    return {
        "type": "node",
        "id": identifier,
        "lat": 34.0209,
        "lon": -6.8416,
        "tags": {"amenity": "pharmacy", "name": "Fixture Étoile", **tags},
    }


def fake_payload(elements: list | None = None, **extra: object) -> bytes:
    """Synthetic network payload, with an explicitly test-only timestamp."""
    return json.dumps(
        {
            "elements": elements or [],
            "osm3s": {"timestamp_osm_base": "2026-01-01T00:00:00Z"},
            **extra,
        }
    ).encode()


def test_normalization_preserves_identity_without_inference(config: dict) -> None:
    """Merge known city variants, not neighborhood guesses or query labels."""
    assert normalize_name("  Pharmacie ÉTOILE  ") == "pharmacie etoile"
    assert normalize_name("الصَّيْدَلِيَّـة") == normalize_name("الصيدلية")
    aliases = {
        normalize_name(key): value for key, value in config["city_aliases"].items()
    }
    assert normalize_city("RABAT الرباط", aliases) == "Rabat"
    assert normalize_city("Marrakech ⵎⵕⵕⴰⴽⵡⵛ مراكش", aliases) == "Marrakech"
    assert normalize_city("Unknown Township", aliases) == "Unknown Township"
    assert normalize_city("113", aliases) is None
    row = record_from_element(element(), "Rabat", aliases)
    assert row is not None and row.city is None
    assert row.is_on_duty is None and row.opening_hours is None
    assert row.phones_e164 == [] and row.query_regions == ["Rabat"]


def test_phones_use_library_example_not_real_business_contact() -> None:
    """Metadata-valid sample numbers exercise formatting, never ownership claims."""
    sample = phonenumbers.example_number("MA")
    assert sample is not None
    national = phonenumbers.format_number(
        sample, phonenumbers.PhoneNumberFormat.NATIONAL
    )
    e164 = phonenumbers.format_number(sample, phonenumbers.PhoneNumberFormat.E164)
    valid, rejected = normalize_phones([f"{national}; {e164};not-a-phone"])
    assert valid == [e164]
    assert rejected == ["not-a-phone"]
    assert normalize_phones(["+442083661177"])[0] == []


@pytest.mark.parametrize(
    "coords",
    [
        {},
        {"lat": None, "lon": -6},
        {"lat": math.nan, "lon": -6},
        {"lat": 91, "lon": 0},
        {"lat": True, "lon": 0},
        {"lat": 0, "lon": 181},
    ],
)
def test_invalid_or_missing_coordinates_dropped(coords: dict) -> None:
    """Invalid locations must not become false nearby results."""
    candidate = element()
    candidate.pop("lat")
    candidate.pop("lon")
    candidate.update(coords)
    assert record_from_element(candidate, "Morocco", {}) is None


def test_way_center_and_bad_center() -> None:
    """Polygon centers are usable without pretending they identify an entrance."""
    candidate = element()
    candidate.update(type="way", center={"lat": 34, "lon": -6})
    row = record_from_element(candidate, "Morocco", {})
    assert row is not None and row.latitude == 34
    candidate["center"] = None
    assert record_from_element(candidate, "Morocco", {}) is None


def test_dedupe_is_conservative_and_preserves_sources(config: dict) -> None:
    """Repeated IDs and nearby names merge, conflicting/distant businesses do not."""
    first = element(1)
    second = element(2)
    second["lat"] += 0.00001
    far = element(3)
    far["lat"] += 1
    conflict = element(4, **{"addr:city": "Elsewhere"})
    first["tags"]["addr:city"] = "Rabat"
    records, stats = clean_elements(
        [(first, "A"), (first, "B"), (second, "A"), (far, "A"), (conflict, "A")], config
    )
    assert stats["duplicate_source_ids"] == 1
    assert stats["merged_map_objects"] == 1
    assert len(records) == 3
    merged = next(row for row in records if len(row.source_ids) == 2)
    assert merged.source_ids == ["node/1", "node/2"]
    assert merged.query_regions == ["A", "B"]
    generic_a, generic_b = element(10, name="Pharmacie"), element(11, name="Pharmacie")
    assert len(clean_elements([(generic_a, "A"), (generic_b, "A")], config)[0]) == 2


def test_deduplication_preserves_phone_and_hours_conflicts(config: dict) -> None:
    """Same-name points with different schedules must remain separate."""
    first = element(1, opening_hours="Mo-Fr 09:00-17:00")
    second = element(2, opening_hours="24/7")
    rows, stats = clean_elements([(first, "A"), (second, "A")], config)
    assert len(rows) == 2 and stats["merged_map_objects"] == 0
    assert all(row.is_on_duty is None for row in rows)


@pytest.fixture
def repository(tmp_path: Path, config: dict) -> PharmacyRepository:
    """Synthetic pharmacies near three representative city coordinates."""
    entries = []
    for index, (city, (lat, lon)) in enumerate(CENTERS.items(), 1):
        candidate = element(index, **{"name:ar": "صيدلية اختبار", "addr:city": city})
        candidate.update(lat=lat + 0.001, lon=lon + 0.001)
        entries.append((candidate, "synthetic_unit_test"))
    rows, _ = clean_elements(entries, config)
    repo = PharmacyRepository(tmp_path / "directory.sqlite3", config["city_aliases"])
    repo.replace_all(rows)
    return repo


@pytest.mark.parametrize("city", CENTERS)
def test_nearest_rabat_casablanca_marrakech(
    repository: PharmacyRepository, city: str
) -> None:
    """Nearest results are sorted, bounded, and associated with the nearby fixture."""
    results = repository.nearest(*CENTERS[city], k=3)
    assert results[0].pharmacy.city == city
    assert 0 < results[0].distance_km < 1
    assert [row.distance_km for row in results] == sorted(
        row.distance_km for row in results
    )
    assert len(results) == 3


def test_spherical_distance_handles_antimeridian() -> None:
    """Longitude wrap must not turn a short path into almost a full circumference."""
    assert haversine_km(0, 179, 0, -179) == pytest.approx(222.39016, rel=0.00001)
    assert haversine_km(34, -6, 34, -6) == pytest.approx(0)


def test_city_and_name_queries_are_literal_and_normalized(
    repository: PharmacyRepository,
) -> None:
    """Arabic/accent search works; wildcards and SQL text remain literal data."""
    assert len(repository.search_by_name("ETOILE")) == 3
    assert len(repository.search_by_name("صيدلية اختبار")) == 3
    assert len(repository.by_city("الرباط")) == 1
    assert repository.by_city("unknown") == []
    assert repository.search_by_name("%") == []
    assert repository.search_by_name("_' OR 1=1 --") == []
    assert repository.search_by_name("   ") == []
    assert repository.metadata()["rows"] == 3


@pytest.mark.parametrize("k", [0, -1, 101, True, 2.5])
def test_nearby_rejects_bad_limits(repository: PharmacyRepository, k: object) -> None:
    """Reject nonsensical and unbounded result counts."""
    with pytest.raises(ValueError):
        repository.nearest(34, -6, k=k)


@pytest.mark.parametrize(
    "lat,lon", [(math.nan, 0), (0, math.inf), (91, 0), (0, 181), (True, 0)]
)
def test_nearby_rejects_bad_coordinates(
    repository: PharmacyRepository, lat: float, lon: float
) -> None:
    """Reject invalid coordinates rather than producing arbitrary orderings."""
    with pytest.raises(ValueError):
        repository.nearest(lat, lon)


def test_missing_db_is_not_created_and_snapshot_replace_is_atomic(
    tmp_path: Path, repository: PharmacyRepository
) -> None:
    """Read typos fail and bad replacements leave the prior snapshot intact."""
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(FileNotFoundError):
        PharmacyRepository(path).all()
    assert not path.exists()
    rows = repository.all()
    with pytest.raises(sqlite3.IntegrityError):
        repository.replace_all([rows[0], rows[0]])
    assert len(repository.all()) == 3
    repository.replace_all([])
    assert repository.nearest(34, -6) == []


def test_query_building_and_explicit_scope() -> None:
    """National queries and bbox queries have distinct, validated selectors."""
    assert "ISO3166-1" in fetch.build_query(120)
    assert "(33.9,-6.95,34.1,-6.7)" in fetch.build_query(120, [33.9, -6.95, 34.1, -6.7])
    with pytest.raises(ValueError):
        fetch.build_query(120, [35, 0, 30, 2])
    with pytest.raises(ValueError):
        fetch.build_query(120, [math.nan, 0, 1, 2])


@pytest.mark.parametrize(
    "raw", [b"not JSON", b"{}", b'{"elements":[null]}', fake_payload(remark="timeout")]
)
def test_partial_or_invalid_overpass_response_rejected(raw: bytes) -> None:
    """Do not publish incomplete payloads as a successful coverage snapshot."""
    with pytest.raises(fetch.FetchError):
        fetch.validate_payload(raw)


def test_http_backoff_respects_retry_after(
    monkeypatch: pytest.MonkeyPatch, config: dict
) -> None:
    """429 is retried sequentially after the server cooldown, not immediately."""
    waits = []
    calls = []

    def mocked_urlopen(request: object, **kwargs: object) -> io.BytesIO:
        calls.append(request)
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                "https://example.invalid", 429, "busy", {"Retry-After": "70"}, None
            )
        return io.BytesIO(fake_payload())

    monkeypatch.setattr(fetch.urllib.request, "urlopen", mocked_urlopen)
    monkeypatch.setattr(fetch, "respectful_sleep", waits.append)
    config["attempts"] = 2
    assert fetch.request_overpass("test query", config) == fake_payload()
    assert waits == [70] and len(calls) == 2


def test_nonretryable_http_and_cooldown_chunks(
    monkeypatch: pytest.MonkeyPatch, config: dict
) -> None:
    """403 aborts; long waits are chunked to permit progress reporting."""

    def forbidden(*args: object, **kwargs: object) -> None:
        raise urllib.error.HTTPError(
            "https://example.invalid", 403, "forbidden", {}, None
        )

    monkeypatch.setattr(fetch.urllib.request, "urlopen", forbidden)
    with pytest.raises(fetch.FetchError, match="HTTP 403"):
        fetch.request_overpass("test", config)
    waits = []
    monkeypatch.setattr(fetch.time, "sleep", waits.append)
    fetch.respectful_sleep(65)
    assert waits == [30, 30, 5]


def test_cache_reuse_hashes_and_bbox_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config: dict
) -> None:
    """Cache hits avoid requests; corrupt bytes and scope changes fail."""
    calls = []

    def mocked_request(query: str, config: dict) -> bytes:
        calls.append(query)
        return fake_payload([element()])

    monkeypatch.setattr(fetch, "request_overpass", mocked_request)
    snapshot = tmp_path / "snapshot"
    manifest_path = fetch.fetch_snapshot(config, snapshot, ["Rabat"])
    assert fetch.fetch_snapshot(config, snapshot, ["Rabat"]) == manifest_path
    assert len(calls) == 1
    manifest = json.loads(manifest_path.read_text())
    assert manifest["scope"] == "selected_bounding_boxes_only"
    with pytest.raises(ValueError, match="different scope"):
        fetch.fetch_snapshot(config, snapshot)
    (snapshot / "region_1.json").write_bytes(b"corrupt")
    with pytest.raises(fetch.FetchError, match="SHA256"):
        fetch.fetch_snapshot(config, snapshot, ["Rabat"])


def test_zero_denominator_metrics_and_report(tmp_path: Path) -> None:
    """An empty directory is explicit, with no NaN or fabricated completeness."""
    metrics = coverage_metrics([], {"retained": 0})
    assert metrics["overall"]["rows"] == 0
    assert set(metrics["overall"]["percent"].values()) == {0.0}
    metrics["source"] = {"scope": "test", "requested_regions": [], "responses": []}
    path = tmp_path / "report.md"
    write_report(metrics, path)
    assert "Denominator: 0" in path.read_text()


@pytest.fixture(scope="module")
def real_snapshot(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict, PharmacyRepository, Path]:
    """Build from checked-in real bytes offline, in an isolated temporary directory."""
    directory = tmp_path_factory.mktemp("real_osm_snapshot")
    config = fetch.load_config(ROOT / "configs/pharmacies.yaml")
    config.update(
        csv_path=str(directory / "pharmacies.csv"),
        database_path=str(directory / "db.sqlite3"),
        metrics_path=str(directory / "metrics.json"),
        report_path=str(directory / "report.md"),
    )
    manifest = ROOT / "data/raw/osm_snapshot/manifest.json"
    metrics = build_directory(manifest, config)
    return (
        metrics,
        PharmacyRepository(Path(config["database_path"]), config["city_aliases"]),
        directory,
    )


@pytest.mark.parametrize("city", CENTERS)
def test_real_directory_nearest_smoke(real_snapshot: tuple, city: str) -> None:
    """Real queries around all three city anchors must find nearby locations."""
    metrics, repository, _ = real_snapshot
    results = repository.nearest(*CENTERS[city], k=3)
    assert len(results) == 3
    assert results[0].distance_km < 10
    expected = metrics["nearest_smoke"][city]
    assert [row.pharmacy.id for row in results] == [row["id"] for row in expected]
    assert all(row.pharmacy.is_on_duty is None for row in results)


def test_real_report_and_saved_counts_reproduce(real_snapshot: tuple) -> None:
    """All committed coverage figures must be traceable to saved source bytes."""
    metrics, repository, directory = real_snapshot
    saved = json.loads((ROOT / "docs/pharmacy_coverage.json").read_text())
    assert metrics == saved
    assert repository.metadata()["rows"] == saved["overall"]["rows"] > 0
    assert (directory / "report.md").read_text() == (
        ROOT / "docs/data_pharmacies.md"
    ).read_text()
    manifest = saved["source"]
    for response in manifest["responses"]:
        raw = (ROOT / "data/raw/osm_snapshot" / response["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == response["sha256"]
