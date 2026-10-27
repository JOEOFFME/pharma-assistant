"""Radius completeness, geodesic perimeter, and map API validation checks."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app
from pharma_assistant.api.pharmacy_map import make_map, radius_ring
from pharma_assistant.data.pharmacies import PharmacyRepository, haversine_km
from pharma_assistant.data_tools.clean_pharmacies import record_from_element


@pytest.fixture
def directory(tmp_path, monkeypatch):
    """Use explicitly synthetic fixtures, never production pharmacy facts."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("API_KEY", raising=False)
    repository = PharmacyRepository(Path("data/pharmacies/pharmacies.sqlite3"))
    rows = []
    for identifier in range(30):
        row = record_from_element(
            {
                "type": "node",
                "id": identifier,
                "lat": 34 + identifier * 0.001,
                "lon": -6,
                "tags": {"amenity": "pharmacy", "name": f"Fixture {identifier}"},
            },
            "Test only",
            {},
        )
        rows.append(row)
    repository.replace_all(rows)
    return repository


def test_radius_is_complete_sorted_and_inclusive(directory):
    rows = directory.within_radius(34, -6, 2)
    assert len(rows) == 18  # > default nearby k; filter all records first.
    assert rows[0].distance_km == 0
    assert all(row.distance_km <= 2 for row in rows)
    boundary = rows[-1].distance_km
    assert len(directory.within_radius(34, -6, boundary)) == 18
    assert directory.within_radius(0, 0, 1) == []


@pytest.mark.parametrize("radius", [0, -1, 101, float("nan"), float("inf"), True])
def test_invalid_radius(directory, radius):
    with pytest.raises(ValueError):
        directory.within_radius(34, -6, radius)


def test_ring_and_empty_figure():
    lats, lons = radius_ring(34, -6, 5)
    assert len(lats) == len(lons) == 73
    assert all(
        haversine_km(34, -6, lat, lon) == pytest.approx(5)
        for lat, lon in zip(lats, lons, strict=False)
    )
    figure = make_map([], 34, -6, 5)
    assert figure["layout"]["map"]["style"] == "open-street-map"
    assert figure["data"][-1]["lat"] == [34]


def test_api_map_matches_records_and_local_bundle(directory):
    with TestClient(create_app()) as client:
        response = client.get("/v1/pharmacies/map?lat=34&lon=-6&radius_km=2")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(data["pharmacies"]) == 18
        markers = data["figure"]["data"][0]
        assert len(markers["lat"]) == len(markers["customdata"]) == 18
        assert markers["customdata"][0] == ["0.00 km", "Inconnu", "Inconnus"]
        assert data["pharmacies"][0]["pharmacy"]["is_on_duty"] is None
        assert data["disclaimer"]
        assert client.get("/assets/plotly.min.js").status_code == 200
        assert client.get("/v1/pharmacies/map?lat=0&lon=0").json()["count"] == 0


@pytest.mark.parametrize(
    "query",
    [
        "lat=91&lon=0",
        "lat=0&lon=181",
        "lat=nan&lon=0",
        "lat=0&lon=0&radius_km=0",
        "lat=0&lon=0&radius_km=101",
    ],
)
def test_api_rejects_invalid_queries(directory, query):
    with TestClient(create_app()) as client:
        assert client.get("/v1/pharmacies/map?" + query).status_code == 422


def test_missing_directory_and_key_guard(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_KEY", "fixture-key")
    with TestClient(create_app()) as client:
        assert client.get("/v1/pharmacies/map?lat=34&lon=-6").status_code == 401
        response = client.get(
            "/v1/pharmacies/map?lat=34&lon=-6", headers={"X-API-Key": "fixture-key"}
        )
        assert response.status_code == 503
        assert client.get("/assets/plotly.min.js").status_code == 200
