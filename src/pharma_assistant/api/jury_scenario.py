"""Explicitly fictional jury fixtures; never used by the normal assistant routes."""

from pathlib import Path

from pharma_assistant.api.answers import MESSAGES
from pharma_assistant.api.schemas import DISCLAIMER, Language
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.nlp.intent import contains_medical_advice
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
            "Cette question ne correspond pas aux demandes prévues du scénario. "
            "Voulez-vous la liste des pharmacies, le stock de Panadol à Al Irfane "
            "ou la pharmacie de garde du scénario ? Ces données ne s’appliquent "
            "pas à une autre ville, un autre produit ou une autre date."
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
            "Had sou2al ma kaytabe9ch les questions dyal scénario. Bghiti list "
            "dyal pharmacies, stock Panadol f Al Irfane wla la garde dyal scénario ? "
            "Had données ma katsla7ch l mdina, dwa wla date okhra."
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
            "هذا السؤال لا يطابق أسئلة السيناريو. هل تريد قائمة الصيدليات أو "
            "مخزون Panadol في Al Irfane أو صيدلية حراسة السيناريو؟ لا تنطبق هذه "
            "البيانات على مدينة أو دواء أو تاريخ آخر."
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

    # Only complete rehearsed questions may disclose fixture facts. Broad keyword
    # matching silently discards changed city, pharmacy, date or medicine qualifiers.
    question_kind = next(
        (
            kind
            for kind, questions in scenario["questions"].items()
            if normalized in {normalize(q, arabizi=False).text for q in questions}
        ),
        None,
    )

    def describe(pharmacy: dict) -> str:
        return (
            f"{pharmacy['name']}\n{pharmacy['address']}\n"
            f"{copy['distance']} : {pharmacy['distance_m']} m"
        )

    if contains_medical_advice(text, config):
        answer = MESSAGES.get(language, MESSAGES["fr"])["refusal"]
        kind = "medical_boundary"
    elif question_kind == "duty":
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
    elif question_kind == "stock":
        records = [p for p in pharmacies if p["id"] == "demo_irfane"]
        pharmacy = records[0]
        answer = copy["stock"].format(count=pharmacy["stock"]["Panadol"])
        answer += "\n\n" + describe(pharmacy)
        kind = "stock"
    elif question_kind == "nearby":
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
        "matched_question": question_kind is not None,
        "origin": scenario["origin"],
        "language": language,
        "transcript": None,
        "actions": [],
        "pharmacies": [{**p, "synthetic": True} for p in records],
        "disclaimer": DISCLAIMER,
    }
