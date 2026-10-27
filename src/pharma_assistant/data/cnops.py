"""Read the attributed CNOPS workbook without treating historical prices as current."""

import json
import re
import unicodedata
import zipfile
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from rapidfuzz import fuzz, process

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


def _exact_search(query, k=5):
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


@lru_cache(maxsize=1)
def spelling_choices():
    """Only use names actually present in the reference as spelling candidates."""
    return sorted(
        {
            normalized(r[f])
            for r in records()
            for f in ("name", "ingredient")
            if re.fullmatch(r"[a-z]{6,30}", normalized(r[f]))
        }
    )


def lookup(query, k=5):
    """Expose uncertain spelling corrections and presentation ambiguity to the model."""
    corrected = normalized(query)
    corrections = []
    rows = _exact_search(corrected, k=500)
    if not rows:
        skip = {
            "medicament",
            "medicaments",
            "recherche",
            "chercher",
            "cherche",
            "quelle",
            "quelles",
            "combien",
            "dosage",
            "comprime",
            "comprimés",
            "presentation",
            "presentations",
            "remboursement",
            "bonjour",
            "cnops",
        }
        for token in re.findall(r"[a-z]{6,30}", corrected):
            if token in skip:
                continue
            choices = process.extract(
                token, spelling_choices(), scorer=fuzz.ratio, score_cutoff=85, limit=2
            )
            if not choices or choices[0][0][:3] != token[:3]:
                continue
            if len(choices) > 1 and choices[0][1] - choices[1][1] < 3:
                continue
            candidate = choices[0][0]
            proposed = re.sub(r"\b" + re.escape(token) + r"\b", candidate, corrected)
            found = _exact_search(proposed, k=500)
            if found:
                corrected, rows = proposed, found
                corrections.append(
                    {"input": token, "candidate": candidate, "needs_confirmation": True}
                )
                break
    variants = {
        (r["name"], r["strength"], r["strength_unit"], r["form"], r["presentation"])
        for r in rows
    }
    return {
        "original_query": query,
        "matched_query": corrected,
        "corrections": corrections,
        "records": rows[:k],
        "match_count": len(rows),
        "presentation_ambiguous": len(variants) > 1,
    }


def search(query, k=5):
    """Return reference candidates; spelling corrections remain explicit in lookup."""
    return lookup(query, k)["records"]
