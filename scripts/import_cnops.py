"""Fetch the public CNOPS resource, retain original bytes and dated provenance."""

import hashlib
import json
from datetime import UTC, datetime
from urllib.request import urlopen

from pharma_assistant.data.cnops import SNAPSHOT, records

API = (
    "https://data.gov.ma/data/api/3/action/package_show?id=referentiel-des-medicaments"
)
RESOURCE_ID = "094733f5-5434-4163-b837-df0e7b665127"


def main():
    """Explicit network operation; never update an old snapshot silently at startup."""
    with urlopen(API, timeout=30) as response:
        data = json.load(response)["result"]
    resource = next(r for r in data["resources"] if r["id"] == RESOURCE_ID)
    with urlopen(resource["url"], timeout=30) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("CNOPS download too large")
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT / "reference.xlsx").write_bytes(raw)
    manifest = {
        "publisher": "CNOPS / Portail Open Data du Maroc",
        "edition": "2014 (source filename)",
        "source_updated": resource["last_modified"][:10],
        "retrieved_on": datetime.now(UTC).date().isoformat(),
        "resource_page": "https://data.gov.ma/data/fr/dataset/referentiel-des-medicaments/resource/"
        + RESOURCE_ID,
        "download_url": resource["url"],
        "license": "ODbL",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "warning": (
            "Historical reference. Never current prices " "or individual entitlement."
        ),
    }
    (SNAPSHOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    records.cache_clear()
    print(
        f"CNOPS source imported: {len(records())} rows; "
        f'edition {manifest["edition"]}; updated {manifest["source_updated"]}.'
    )


if __name__ == "__main__":
    main()
