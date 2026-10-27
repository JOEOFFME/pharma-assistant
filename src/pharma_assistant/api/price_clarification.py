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
        "source_ids": ["cnops_reference"],
        "sources": [
            {
                "id": "cnops_reference",
                "title": "Référentiel CNOPS historique — présentations à préciser",
                "url": row["source_url"],
                "kind": "cnops_record",
            }
        ],
    }


def presentation_followup(text, history=None):
    """Explain a requested package field without choosing a personal dose."""
    if text.casefold().strip(" .?!") not in {
        "dosage",
        "le dosage",
        "c'est quoi dosage",
        "quel dosage",
    }:
        return None
    turns = history or []
    if not turns or turns[-1]["role"] != "assistant":
        return None
    previous = turns[-1]["text"]
    if not re.search(r"présentation|taille.*bo[iî]te|forme.*bo[iî]te", previous, re.I):
        return None
    return {
        "answer": "Par « dosage », je parle du nombre en mg ou en g sur la boîte, "
        "pas de la quantité à prendre. Recopiez le nom commercial, ce nombre, "
        "la forme et la taille de la boîte pour identifier la bonne présentation.",
        "answer_source": "presentation_clarification",
        "pharmacies": [],
        "sources": [],
        "source_ids": [],
        "actions": [],
        "model": None,
    }
