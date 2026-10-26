"""Conservative display/search and Moroccan phone normalization."""

import re
import unicodedata

import phonenumbers


def display_text(value: object) -> str | None:
    """Normalize Unicode/whitespace without translating or inventing source content."""
    if not isinstance(value, str):
        return None
    return " ".join(unicodedata.normalize("NFKC", value).split()) or None


def normalize_name(value: str) -> str:
    """Search key: casefold, accents/diacritics/tatweel and common Arabic variants."""
    value = unicodedata.normalize("NFKD", value).casefold().replace("ـ", "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    return " ".join(value.split())


def normalize_phones(raw_values: list[str]) -> tuple[list[str], list[str]]:
    """Keep only valid Moroccan E.164 numbers; validation does not verify ownership."""
    valid: set[str] = set()
    rejected: set[str] = set()
    for raw in raw_values:
        for part in re.split(r"[;,\n]|\s/\s", raw):
            part = part.strip()
            if not part:
                continue
            try:
                number = phonenumbers.parse(part.removeprefix("tel:"), "MA")
                if number.country_code != 212 or not phonenumbers.is_valid_number(
                    number
                ):
                    rejected.add(part)
                    continue
                valid.add(
                    phonenumbers.format_number(
                        number, phonenumbers.PhoneNumberFormat.E164
                    )
                )
            except phonenumbers.NumberParseException:
                rejected.add(part)
    return sorted(valid), sorted(rejected)


def normalize_city(raw: str | None, aliases: dict[str, str]) -> str | None:
    """Resolve known aliases, including multilingual labels; keep unknown names raw."""
    if raw is None:
        return None
    key = normalize_name(raw)
    if key in {"unknown", "null", "none", "n/a", "?", "maroc", "morocco", "المغرب"}:
        return None
    if not any(char.isalpha() for char in raw):
        return None
    if key in aliases:
        return aliases[key]
    # OSM commonly repeats the city name in Latin/Tifinagh/Arabic in one label.
    # Use the Latin portion only if it matches an explicitly configured alias.
    latin = "".join(
        char if "LATIN" in unicodedata.name(char, "") or char in " '-" else " "
        for char in raw
    )
    return aliases.get(normalize_name(latin), raw)
