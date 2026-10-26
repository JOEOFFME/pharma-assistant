"""Text-to-v1 baseline orchestration; no medical recommendations or live stock."""

import re
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from pharma_assistant.api.schemas import AnalysisResponse, InputInfo
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.matching.medications import MedicationIndex
from pharma_assistant.nlp.entities import EntityExtractor
from pharma_assistant.nlp.intent import classify_intent
from pharma_assistant.nlp.langid import detect_language


class TextPipeline:
    """Initialize explicitly, with no database or network work during import."""

    def __init__(self, config: dict, index: MedicationIndex, cities: dict) -> None:
        self.config = config
        self.extractor = EntityExtractor(
            index, config, Path(config["lexicon_seed"]), cities
        )

    @classmethod
    def from_config(cls, path: Path = Path("configs/baseline.yaml")) -> "TextPipeline":
        """Use locally rebuilt Task-4 catalogue; fail clearly when it is missing."""
        config = load_config(path)
        med = load_config(Path(config["medications_config"]))
        cities = load_config(Path(config["pharmacies_config"]))["city_aliases"]
        index = MedicationIndex.from_database(
            Path(med["database_path"]), med["matching"]
        )
        return cls(config, index, cities)

    def analyze(
        self, text: str, *, language_hint: str | None = None
    ) -> AnalysisResponse:
        """Interpret original text without changing offsets or dispensing advice."""
        started = perf_counter()
        InputInfo(
            modality="text",
            raw_text=text,
            language=language_hint if language_hint is not None else "fr",
        )
        language = language_hint if language_hint is not None else detect_language(text)
        label, mixed, ambiguous_actions = classify_intent(text, self.config)
        entities, relations, uncertain = self.extractor.extract(text)
        meds = [e for e in entities if e["type"] == "MEDICATION"]
        # Preserve explicit rejected products and unresolved alternatives as evidence.
        alternatives = bool(re.search(r"\b(?:ou|ولا)\b", text, re.I))
        for med in meds:
            prefix = text[max(0, med["start"] - 20) : med["start"]]
            if re.search(r"(?:pas|ماشي)\s+$", prefix, re.I):
                med["assertion"] = "negated"
            elif alternatives:
                med["assertion"] = "uncertain"
        by_id = {m["entity_id"]: m for m in meds}
        for entity in entities:
            target = by_id.get(entity.get("medication_ref"))
            if target and target.get("assertion"):
                entity["assertion"] = target["assertion"]
        ambiguous_actions |= alternatives or any(m.get("assertion") for m in meds)
        need = ambiguous_actions or uncertain
        if label in {
            "check_availability",
            "request_medication",
            "price_inquiry",
        } and not any(m.get("assertion", "affirmed") == "affirmed" for m in meds):
            need = True
        directory = {
            "pharmacy_info_phone": "phone",
            "pharmacy_info_location": "location",
            "pharmacy_info_hours": "hours",
        }.get(label)
        locations = [e for e in entities if e["type"] == "LOCATION"]
        if (
            directory
            and not locations
            and not any(e["type"] == "PHARMACY_NAME" for e in entities)
        ):
            need = True
        if label == "out_of_scope":
            need = False
        return AnalysisResponse.model_validate(
            {
                "request_id": str(uuid4()),
                "input": {"modality": "text", "raw_text": text, "language": language},
                "intent": {
                    "label": label,
                    "confidence": float(
                        self.config["fallback_confidence"]
                        if label == "out_of_scope"
                        else self.config["rule_confidence"]
                    ),
                },
                "entities": entities,
                "relations": relations,
                "contains_out_of_scope_request": mixed,
                "pharmacy_query": {
                    "needs_pharmacy_info": directory is not None,
                    "info_type": directory,
                    "location_text": (
                        locations[0]["text"] if directory and locations else None
                    ),
                },
                "needs_clarification": bool(need),
                "clarification_question": {
                    "fr": (
                        "Pouvez-vous préciser le produit ou la demande ?"
                        if need
                        else None
                    )
                },
                "latency_ms": int((perf_counter() - started) * 1000),
            }
        )
