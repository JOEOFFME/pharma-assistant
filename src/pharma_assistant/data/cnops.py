"""Read the attributed CNOPS workbook without treating historical prices as current."""

import json
import re
import unicodedata
import zipfile
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from pharma_assistant.matching.medications import strength_tokens

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "data/raw/cnops_snapshot"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalized(text):
    """Normalize accents and spacing without altering numeric medicine strengths."""
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", text.casefold())
            if not unicodedata.combining(c)
        ).split()
    )


def amount(value):
    """Render source decimal amounts; Excel binary tails are rounded to cents."""
    if value in {None, ""}:
        return None
    try:
        return format(
            Decimal(str(value).replace(",", ".")).quantize(Decimal("0.01")), ".2f"
        )
    except InvalidOperation:
        raise ValueError("Invalid CNOPS monetary cell") from None


def workbook_rows(path):
    """Read the first source sheet, preserving cell columns and empty values."""
    with zipfile.ZipFile(path) as archive:
        if sum(info.file_size for info in archive.infolist()) > 64 * 1024 * 1024:
            raise ValueError("CNOPS workbook too large")
        strings = [
            "".join(node.itertext())
            for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                "s:si", NS
            )
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        headers = None
        for row in sheet.findall("s:sheetData/s:row", NS):
            cells = {}
            for cell in row.findall("s:c", NS):
                value = cell.find("s:v", NS)
                if value is None:
                    continue
                column = re.sub(r"\d", "", cell.attrib["r"])
                cells[column] = (
                    strings[int(value.text)]
                    if cell.attrib.get("t") == "s"
                    else value.text
                )
            if headers is None:
                headers = cells
                if not {"CODE", "NOM", "DCI1", "PPV", "PRIX_BR"} <= set(
                    headers.values()
                ):
                    raise ValueError("Unrecognized CNOPS headers")
                continue
            if cells.get("A") and cells.get("B"):
                yield {key: cells.get(column, "") for column, key in headers.items()}


@lru_cache(maxsize=1)
def records():
    """Load immutable source rows, not inferred authorization/clinical indications."""
    manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    output = []
    for index, row in enumerate(workbook_rows(SNAPSHOT / "reference.xlsx"), start=2):
        output.append(
            {
                "id": f'cnops:{row["CODE"]}:{index}',
                "ean": row["CODE"],
                "name": row["NOM"],
                "ingredient": row["DCI1"],
                "strength": row.get("DOSAGE1"),
                "strength_unit": row.get("UNITE_DOSAGE1"),
                "form": row.get("FORME"),
                "presentation": row.get("PRESENTATION"),
                "ppv_mad": amount(row.get("PPV")),
                "hospital_price_mad": amount(row.get("PH")),
                "reimbursement_base_mad": amount(row.get("PRIX_BR")),
                "source_reimbursement_rate": row.get("TAUX_REMBOURSEMENT"),
                "princeps_generic": row.get("PRINCEPS_GENERIQUE"),
                "edition": manifest["edition"],
                "source_updated": manifest["source_updated"],
                "retrieved_on": manifest["retrieved_on"],
                "source_url": manifest["resource_page"],
                "historical": True,
            }
        )
    return output


def search(query, k=5):
    """Return literal name/DCI matches; do not invent a match for absent brands."""
    needle = normalized(query)
    matched = []
    for record in records():
        name, ingredient = normalized(record["name"]), normalized(record["ingredient"])

        def mentioned(value):
            return bool(
                value and re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", needle)
            )

        if mentioned(name) or mentioned(ingredient):
            requested = strength_tokens(needle)
            description = " ".join(
                str(record.get(f) or "") for f in ["name", "strength", "strength_unit"]
            )
            if requested and not requested <= strength_tokens(description):
                continue
            form = normalized(record["form"] or "")
            if any(
                term in needle and term not in form
                for term in ["comprime", "gelule", "suppositoire", "sirop"]
            ):
                continue
            matched.append(record)
    return matched[:k]
