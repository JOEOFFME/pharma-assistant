"""Medication schema and SQLite storage with explicit source provenance."""

import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class MedicationSource(BaseModel):
    """The reference jurisdiction and source date do not imply local availability."""

    model_config = ConfigDict(extra="forbid")
    dataset: str
    country: str
    url: str
    license_url: str
    source_id: str
    source_updated: str
    raw_sha256: str


class MedicationAlias(BaseModel):
    """Generated spellings are distinguished from observed source names."""

    text: str
    kind: str
    synthetic: bool


class MedicationRecord(BaseModel):
    """One source specialty, not a dispensation recommendation or stock record."""

    model_config = ConfigDict(extra="forbid")
    id: str
    brand_name: str
    brand_name_ar: str | None = None
    full_name: str
    dci: str | None = None
    dosage: str | None = None
    form: str | None = None
    presentation: str | None = None
    laboratory: str | None = None
    price_ppv: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    source: MedicationSource
    aliases: list[MedicationAlias]
    composition: list[dict[str, str]] = Field(default_factory=list)
    authorization_status: str | None = None
    marketing_status: str | None = None


class MedicationRepository:
    """Persist complete records and a relational medication/alias inventory."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def replace_all(self, rows: list[MedicationRecord]) -> None:
        """Replace all records atomically; identifiers include the source namespace."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS medications (
                    id TEXT PRIMARY KEY, brand_name TEXT NOT NULL, brand_name_ar TEXT,
                    dci TEXT, dosage TEXT, form TEXT,
                    presentation TEXT, laboratory TEXT,
                    price_ppv REAL, source TEXT NOT NULL, record_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS medication_aliases (
                    medication_id TEXT NOT NULL, alias TEXT NOT NULL,
                    kind TEXT NOT NULL, synthetic INTEGER NOT NULL,
                    PRIMARY KEY(medication_id,alias)
                );
            """
            )
            connection.execute("DELETE FROM medication_aliases")
            connection.execute("DELETE FROM medications")
            connection.executemany(
                "INSERT INTO medications VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        row.id,
                        row.brand_name,
                        row.brand_name_ar,
                        row.dci,
                        row.dosage,
                        row.form,
                        row.presentation,
                        row.laboratory,
                        row.price_ppv,
                        row.source.model_dump_json(),
                        row.model_dump_json(),
                    )
                    for row in rows
                ],
            )
            connection.executemany(
                "INSERT INTO medication_aliases VALUES (?,?,?,?)",
                [
                    (row.id, alias.text, alias.kind, int(alias.synthetic))
                    for row in rows
                    for alias in row.aliases
                ],
            )

    def all(self) -> list[MedicationRecord]:
        """Read typed records; a typo must not create a blank database."""
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            return [
                MedicationRecord.model_validate_json(item[0])
                for item in connection.execute(
                    "SELECT record_json FROM medications ORDER BY id"
                )
            ]
