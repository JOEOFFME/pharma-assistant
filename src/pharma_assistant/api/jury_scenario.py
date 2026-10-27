"""Explicitly fictional jury fixtures; never used by the normal assistant routes."""

from pathlib import Path

from pharma_assistant.api.answers import MESSAGES
from pharma_assistant.api.schemas import DISCLAIMER, Language
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.nlp.intent import contains_medical_advice, phrase_in
from pharma_assistant.nlp.langid import detect_language
from pharma_assistant.nlp.normalize import normalize

ROOT = Path(__file__).resolve().parents[3]
WARNING = "Démonstration — données fictives, sans confirmation réelle."

COPY = {
    "fr": {
        "nearby": (
            "Pharmacies du scénario, depuis le point de départ fictif Al Irfane :"
        ),
        "stock": (
            "Oui, dans ce scénario, Panadol est disponible à la Pharmacie Al Irfane "
            "(fictive) : {count} boîtes en stock simulé."
        ),
        "duty": "La pharmacie de garde pour la nuit du scénario est :",
        "hours": "Garde simulée : {hours}, pendant la nuit du scénario.",
        "help": (
            "Ce scénario contient trois pharmacies fictives. Demandez la liste des "
            "plus proches, le stock de Panadol à Al Irfane ou la pharmacie de garde. "
            "Il ne contient aucun autre stock, prix ou horaire réel."
        ),
        "distance": "Distance simulée",
    },
    "darija_latn": {
        "nearby": (
            "Hadi list dyal a9rab pharmacies f scénario, "
            "men point fictif Al Irfane :"
        ),
        "stock": (
            "Ah, f had scénario, Panadol kayn f Pharmacie Al Irfane (fictive) : "
            "{count} boîtes f stock simulé."
        ),
        "duty": "F had scénario, pharmacie li dayra la garde hiya :",
        "hours": "Garde simulée : {hours}, f lil dyal scénario.",
        "help": (
            "Had scénario fih 3 pharmacies fictives. Sowel 3la a9rab pharmacies, "
            "stock Panadol f Al Irfane wla pharmacie de garde. "
            "Ma fihch stock, taman wla horaires réels."
        ),
        "distance": "Distance simulée",
    },
    "ar": {
        "nearby": "صيدليات السيناريو حسب قربها من نقطة انطلاق افتراضية:",
        "stock": (
            "نعم، في هذا السيناريو يتوفر Panadol في صيدلية Al Irfane الافتراضية: "
            "{count} علبة في المخزون المحاكى."
        ),
        "duty": "صيدلية الحراسة في ليلة السيناريو الافتراضي هي:",
        "hours": "حراسة محاكاة: {hours} في ليلة السيناريو.",
        "help": (
            "يتضمن السيناريو ثلاث صيدليات افتراضية. اسأل عن الأقرب أو مخزون "
            "Panadol في Al Irfane أو الحراسة. هذه ليست معلومات واقعية."
        ),
        "distance": "مسافة محاكاة",
    },
}


def scenario_answer(text: str, language_hint: Language | None = None) -> dict:
    """Return reproducible fixture facts, with fiction labels in every answer."""
    language = language_hint or detect_language(text)
    key = "ar" if language in {"ar", "darija_ar"} else language
    copy = COPY.get(key, COPY["fr"])
    warning = (
        "عرض توضيحي — بيانات افتراضية، وليست معلومات مؤكدة عن الواقع."
        if key == "ar"
        else WARNING
    )
    normalized = normalize(text, arabizi=False).text
    config = load_config(ROOT / "configs/baseline.yaml")
    scenario = load_config(ROOT / "configs/jury_scenario.yaml")
    pharmacies = sorted(scenario["pharmacies"], key=lambda p: p["distance_m"])
    records = []
    kind = "help"

    def has(*terms: str) -> bool:
        return any(phrase_in(normalized, term) for term in terms)

    def describe(pharmacy: dict) -> str:
        return (
            f"{pharmacy['name']}\n{pharmacy['address']}\n"
            f"{copy['distance']} : {pharmacy['distance_m']} m"
        )

    if contains_medical_advice(text, config):
        answer = MESSAGES.get(language, MESSAGES["fr"])["refusal"]
        kind = "medical_boundary"
    elif has("garde", "الحراسة", "حراسة", "المناوبة", "مناوبة"):
        records = [p for p in pharmacies if p["night_shift"]]
        answer = (
            copy["duty"]
            + "\n\n"
            + "\n\n".join(
                describe(p) + "\n" + copy["hours"].format(hours=p["shift_hours"])
                for p in records
            )
        )
        kind = "duty"
    elif (
        has("Panadol", "بانادول")
        and has("irfane", "irfan", "alirfane", "العرفان", "إرفان")
        and not has("prix", "taman", "bch7al", "ثمن", "سعر", "بشحال")
    ):
        records = [p for p in pharmacies if p["id"] == "demo_irfane"]
        pharmacy = records[0]
        answer = copy["stock"].format(count=pharmacy["stock"]["Panadol"])
        answer += "\n\n" + describe(pharmacy)
        kind = "stock"
    elif has(
        "a9rab", "aqrab", "proches", "proche", "nearby", "nearest", "أقرب", "اقرب"
    ) and has("pharmacy", "pharmacies", "pharmacie", "pharmachie", "صيدلية", "صيدليات"):
        records = pharmacies
        answer = (
            copy["nearby"]
            + "\n\n"
            + "\n\n".join(f"{i}. {describe(p)}" for i, p in enumerate(records, 1))
        )
        kind = "nearby"
    else:
        answer = copy["help"]
    return {
        "answer": warning + "\n\n" + answer,
        "synthetic": True,
        "scenario": "jury_al_irfane_v1",
        "scenario_kind": kind,
        "origin": scenario["origin"],
        "language": language,
        "transcript": None,
        "actions": [],
        "pharmacies": [{**p, "synthetic": True} for p in records],
        "disclaimer": DISCLAIMER,
    }
