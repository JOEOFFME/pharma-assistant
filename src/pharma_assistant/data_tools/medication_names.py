"""Deterministic synthetic spelling aliases; no ingredient or equivalence inference."""

import re
import unicodedata

ARABIC_TO_LATIN = str.maketrans(
    {
        "ا": "a",
        "أ": "a",
        "إ": "i",
        "آ": "a",
        "ب": "b",
        "ت": "t",
        "ث": "th",
        "ج": "j",
        "ح": "h",
        "خ": "kh",
        "د": "d",
        "ذ": "dh",
        "ر": "r",
        "ز": "z",
        "س": "s",
        "ش": "ch",
        "ص": "s",
        "ض": "d",
        "ط": "t",
        "ظ": "z",
        "ع": "a",
        "غ": "gh",
        "ف": "f",
        "ق": "q",
        "ك": "k",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ه": "h",
        "ة": "a",
        "و": "o",
        "ي": "i",
        "ى": "a",
        "ء": "",
        "ـ": "",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
)


def basic_normalize(text: str) -> str:
    """Casefold/accent-fold strings and Arabic numeric glyphs, preserving amounts."""
    text = unicodedata.normalize("NFKD", text).casefold()
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.translate(ARABIC_TO_LATIN)
    return " ".join(re.sub(r"[^a-z0-9%.,/]+", " ", text).split())


def phonetic_key(text: str) -> str:
    """Approximate cross-script retrieval key, deliberately not an identity function."""
    text = basic_normalize(text)
    tokens = []
    for token in text.split():
        if re.search(r"[a-z]", token):
            token = token.translate(str.maketrans({"3": "a", "7": "h", "9": "q"}))
            for source, target in [("ph", "f"), ("ou", "o"), ("qu", "k"), ("ch", "sh")]:
                token = token.replace(source, target)
            token = (
                re.sub(r"c(?=[eiy])", "s", token).replace("c", "k").replace("p", "b")
            )
            token = re.sub(r"e$", "", token)
        tokens.append(token)
    return " ".join(tokens)


def latin_to_arabic(text: str) -> str:
    """Generate a rough Arabic-script spelling; always label it synthetic."""
    text = basic_normalize(text)
    for source, target in [("ph", "ف"), ("ch", "ش"), ("ou", "و"), ("qu", "ك")]:
        text = text.replace(source, target)
    text = re.sub(r"e\b", "", text)
    table = str.maketrans(
        dict(
            zip(
                "abcdefghijklmnopqrstuvwxyz",
                [
                    "ا",
                    "ب",
                    "ك",
                    "د",
                    "ي",
                    "ف",
                    "غ",
                    "ه",
                    "ي",
                    "ج",
                    "ك",
                    "ل",
                    "م",
                    "ن",
                    "و",
                    "ب",
                    "ك",
                    "ر",
                    "س",
                    "ت",
                    "و",
                    "ف",
                    "و",
                    "كس",
                    "ي",
                    "ز",
                ],
                strict=True,
            )
        )
    )
    return text.translate(table)


def generate_aliases(brand: str, name: str, dosage: str | None) -> list[dict]:
    """Keep source spellings distinct from programmatic spelling/noise variants."""
    variants: dict[str, dict] = {}

    def add(text: str, kind: str, synthetic: bool) -> None:
        if text and text not in variants:
            variants[text] = {"text": text, "kind": kind, "synthetic": synthetic}

    for text in [brand, name]:
        add(text, "source", False)
        add(text.lower(), "lowercase", True)
        add(basic_normalize(text), "accent_fold", True)
    add(latin_to_arabic(brand), "arabic_transliteration", True)
    add(phonetic_key(brand), "phonetic", True)
    base = basic_normalize(brand)
    if len(base) >= 5:
        add(base[:-1], "deletion", True)
        middle = len(base) // 2
        add(
            base[:middle] + base[middle + 1] + base[middle] + base[middle + 2 :],
            "transposition",
            True,
        )
        # Arabizi numerals are generated in lexical tokens, not strength digits.
        arabizi = base.replace("a", "3").replace("h", "7").replace("q", "9")
        add(arabizi, "arabizi", True)
    if dosage:
        add(f"{brand} {dosage}", "brand_strength", True)
    return sorted(variants.values(), key=lambda item: item["text"])
