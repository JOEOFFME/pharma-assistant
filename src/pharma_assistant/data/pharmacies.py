"""Typed pharmacy records and parameterized SQLite queries."""

import math
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from pharma_assistant.data_tools.pharmacy_normalize import normalize_name


class PharmacyRecord(BaseModel):
    """Provenance-bearing directory record; unknown duty status stays null."""

    model_config = ConfigDict(extra="forbid")
    id: str
    name: str | None
    name_ar: str | None
    name_fr: str | None
    aliases: list[str]
    city: str | None
    city_raw: list[str]
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    phones_e164: list[str]
    phones_raw: list[str]
    rejected_phones: list[str]
    opening_hours: str | None
    hours_variants: list[str]
    source_ids: list[str]
    source_urls: list[str]
    query_regions: list[str]
    data_quality: Annotated[float, Field(ge=0, le=1)]
    is_on_duty: bool | None = None
    duty_from: str | None = None
    duty_to: str | None = None


class NearbyPharmacy(BaseModel):
    """Straight-line center-to-point distance; not a road route or availability."""

    pharmacy: PharmacyRecord
    distance_km: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance on a sphere (mean Earth radius 6371.0088 km)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = phi2 - phi1, math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def validate_limit(limit: int) -> None:
    """Keep interactive queries bounded and reject booleans masquerading as counts."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit/k must be an integer between 1 and 100")


class PharmacyRepository:
    """Small-snapshot repository; nearby search scans coordinates deterministically."""

    def __init__(
        self, database_path: Path, city_aliases: dict[str, str] | None = None
    ) -> None:
        """Remember configuration without implicitly creating a database."""
        self.database_path = database_path
        self.city_aliases = {
            normalize_name(k): v for k, v in (city_aliases or {}).items()
        }

    def _connect(self, *, write: bool = False) -> sqlite3.Connection:
        """Read operations must not silently create an empty file on a typo."""
        if not write and not self.database_path.is_file():
            raise FileNotFoundError(self.database_path)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def replace_all(self, records: list[PharmacyRecord]) -> None:
        """Atomically replace a snapshot and clear obsolete rows on rebuild."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect(write=True)) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS pharmacies (
                    id TEXT PRIMARY KEY, name TEXT, name_ar TEXT, name_fr TEXT,
                    city TEXT, city_key TEXT NOT NULL, search_name TEXT NOT NULL,
                    latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
                    longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
                    phone_e164 TEXT, opening_hours TEXT,
                    data_quality REAL NOT NULL CHECK(data_quality BETWEEN 0 AND 1),
                    is_on_duty INTEGER CHECK(is_on_duty IN (0,1) OR is_on_duty IS NULL),
                    duty_from TEXT, duty_to TEXT, record_json TEXT NOT NULL
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_pharmacy_city ON pharmacies(city_key)"
            )
            connection.execute("DELETE FROM pharmacies")
            connection.executemany(
                "INSERT INTO pharmacies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        row.id,
                        row.name,
                        row.name_ar,
                        row.name_fr,
                        row.city,
                        normalize_name(row.city or ""),
                        " | ".join(normalize_name(name) for name in row.aliases),
                        row.latitude,
                        row.longitude,
                        row.phones_e164[0] if row.phones_e164 else None,
                        row.opening_hours,
                        row.data_quality,
                        row.is_on_duty,
                        row.duty_from,
                        row.duty_to,
                        row.model_dump_json(),
                    )
                    for row in records
                ],
            )

    def _select(self, query: str, parameters: tuple = ()) -> list[PharmacyRecord]:
        """Deserialize complete records without exposing a long-lived connection."""
        with closing(self._connect()) as connection:
            return [
                PharmacyRecord.model_validate_json(row[0])
                for row in connection.execute(query, parameters)
            ]

    def all(self) -> list[PharmacyRecord]:
        """Return the current snapshot in stable source-ID order."""
        return self._select("SELECT record_json FROM pharmacies ORDER BY id")

    def search_by_name(self, name: str, limit: int = 10) -> list[PharmacyRecord]:
        """Search literal normalized substrings without wildcard expansion."""
        validate_limit(limit)
        needle = normalize_name(name)
        if not needle:
            return []
        escaped = needle.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        return self._select(
            "SELECT record_json FROM pharmacies "
            "WHERE search_name LIKE ? ESCAPE '\\' ORDER BY id LIMIT ?",
            (f"%{escaped}%", limit),
        )

    def by_city(self, city: str, limit: int = 100) -> list[PharmacyRecord]:
        """Look up observed addr:city, using optional aliases for query names."""
        validate_limit(limit)
        key = normalize_name(city)
        if not key:
            return []
        key = normalize_name(self.city_aliases.get(key, city))
        return self._select(
            "SELECT record_json FROM pharmacies WHERE city_key=? ORDER BY id LIMIT ?",
            (key, limit),
        )

    def nearest(
        self, latitude: float, longitude: float, k: int = 5
    ) -> list[NearbyPharmacy]:
        """Return nearest stored points, without a city or radius restriction."""
        validate_limit(k)
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError("Coordinates must be finite WGS84 latitude/longitude")
        rows = [
            NearbyPharmacy(
                pharmacy=row,
                distance_km=haversine_km(
                    latitude, longitude, row.latitude, row.longitude
                ),
            )
            for row in self.all()
        ]
        return sorted(rows, key=lambda row: (row.distance_km, row.pharmacy.id))[:k]

    def metadata(self) -> dict[str, object]:
        """Return source-neutral table counts for smoke checks."""
        with closing(self._connect()) as connection:
            total = connection.execute("SELECT COUNT(*) FROM pharmacies").fetchone()[0]
        return {"rows": total, "table": "pharmacies", "schema_version": 1}
