"""Small script/lexicon language heuristics; scores are not calibrated."""

import re

from pharma_assistant.api.schemas import Language
from pharma_assistant.nlp.normalize import normalize

LATN_DARIJA = {
    "wach",
    "kayn",
    "kayna",
    "bghit",
    "3andkom",
    "3ndkom",
    "bch7al",
    "dyal",
    "ch7al",
    "3afak",
    "fin",
    "salam",
    "chokran",
    "n7taj",
    "ntleb",
}
AR_DARIJA = {
    "واش",
    "كاين",
    "كاينة",
    "بغيت",
    "شحال",
    "بشحال",
    "فين",
    "عندكم",
    "ديال",
    "دابا",
    "عافاك",
}
FRENCH = {
    "je",
    "vous",
    "avez",
    "le",
    "la",
    "les",
    "bonjour",
    "merci",
    "prix",
    "sirop",
    "ou",
    "quel",
    "quelle",
    "besoin",
    "disponible",
    "salut",
    "voudrais",
}


def detect_language(text: str) -> Language:
    """Ignore isolated Latin brands/units; distinguish MSA and Darija lexically."""
    plain = normalize(text, arabizi=False).text
    words = set(plain.split())
    arabic = bool(re.search(r"[\u0621-\u064a]", plain))
    darija = bool(words & LATN_DARIJA)
    french = len(words & FRENCH)
    if arabic:
        if french >= 2 or (darija and french):
            return "mixed"
        return "darija_ar" if words & AR_DARIJA else "ar"
    if darija and french:
        return "mixed"
    if darija or re.search(r"\b\d+[a-z]+", plain):
        return "darija_latn"
    return "fr"
