"""Small attributed educational reference cache, independent of live web access."""

import json
import re
from pathlib import Path


def reference_for(text: str, history=None) -> dict | None:
    """Resolve the cached topic only from the question or explicit user follow-ups."""
    topic = r"migraine|الشقيقة|ميكران"
    matched = bool(re.search(topic, text, re.I))
    if (
        not matched
        and len(text) < 100
        and re.search(r"smya|smiya|nom|dyalo|اسم", text, re.I)
    ):
        recent = [t["text"] for t in (history or []) if t["role"] == "user"][-3:]
        matched = any(re.search(topic, t, re.I) for t in recent)
    if not matched:
        return None
    path = Path(__file__).resolve().parents[3] / "data/health/references.json"
    return json.loads(path.read_text(encoding="utf-8"))["migraine"]


def reference_answer(reference: dict, language: str) -> dict:
    """Render a general name from attributed evidence, never a personal prescription."""
    if language == "darija_latn":
        answer = (
            "Sumatriptan smiya dyal dwa kaytsta3mel l crise dyal migraine, "
            "7sab référence NHS msajla. Hada exemple 3am, machi ikhtiyar dwa lik: "
            "ma kaynasbch kolchi. Pharmacien wla tbib y2ekked wach monasib lik. "
            "Hadi référence msajla, machi recherche web jdida "
            "wla confirmation dyal stock."
        )
    elif language in {"ar", "darija_ar"}:
        answer = (
            "سوماتريبتان اسم دواء يُستخدم لنوبات الشقيقة حسب مرجع NHS المحفوظ. "
            "هذا مثال عام وليس اختيار علاج لك؛ فهو لا يناسب الجميع. "
            "يحدد الصيدلي أو الطبيب مدى ملاءمته. هذا مرجع محفوظ وليس بحثًا جديدًا "
            "على الإنترنت أو تأكيدًا لتوفر الدواء."
        )
    else:
        answer = (
            "Le sumatriptan est un exemple de médicament utilisé contre les crises "
            "de migraine, selon la référence NHS enregistrée. C’est une information "
            "générale : il ne convient pas à tout le monde et le choix pour vous "
            "doit être confirmé avec un pharmacien ou un médecin. "
            "Il s’agit d’une référence enregistrée, pas d’une nouvelle recherche "
            "web ni d’une confirmation de disponibilité au Maroc."
        )
    return {
        "answer": answer,
        "sources": reference["sources"],
        "source_ids": [s["id"] for s in reference["sources"]],
        "answer_source": "saved_health_reference",
        "model": None,
    }
