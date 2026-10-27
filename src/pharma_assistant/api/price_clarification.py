"""Keep an ambiguous medicine price request actionable during research failures."""

import re

from pharma_assistant.data.cnops import lookup, normalized


def clarify_price(text, language="fr"):
    """Ask for the actual source presentation, without inventing a price or identity."""
    if not re.search(r"prix|tarif|combien|ch7al|bch7al|ثمن|بشحال", text, re.I):
        return None
    if re.search(r"liste|fourchette|compar|toutes les|tous les", text, re.I):
        return None
    result = lookup(text)
    if not result["records"] or not (
        result["presentation_ambiguous"] or result["corrections"]
    ):
        return None
    row = result["records"][0]
    name = (
        result["corrections"][0]["candidate"]
        if result["corrections"]
        else (
            row["name"]
            if normalized(row["name"]) in normalized(text)
            else row["ingredient"] or row["name"]
        )
    )
    answer = (
        f"Si vous parlez de « {name} », quelle présentation cherchez-vous "
        "(nom commercial, dosage, forme et taille de boîte) ?"
    )
    if language == "darija_latn":
        answer = (
            f"Ila kat9sed « {name} », chno smiya commerciale, dosage, forme "
            "w taille dyal lboita ? Taman kaytbedel 7sab présentation."
        )
    elif language in {"ar", "darija_ar"}:
        answer = (
            f"إذا كنت تقصد « {name} »، فما الاسم التجاري والتركيز والشكل "
            "وحجم العلبة؟ السعر يختلف حسب العرض."
        )
    return {
        "answer": answer,
        "answer_source": "medicine_price_clarification",
        "model": None,
        "pharmacies": [],
        "actions": [],
        "source_ids": [row["id"]],
        "sources": [
            {
                "id": row["id"],
                "title": row["name"] + " (CNOPS historique)",
                "url": row["source_url"],
                "kind": "cnops_record",
            }
        ],
    }
