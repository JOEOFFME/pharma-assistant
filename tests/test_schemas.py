"""Contract and annotation checks; fixtures do not assert real medication facts."""

import copy
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from pharma_assistant.api.schemas import AnalysisResponse, Entity

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples"
SAMPLES = json.loads(
    (EXAMPLES / "response_v1_samples.json").read_text(encoding="utf-8")
)
ANNOTATIONS = json.loads(
    (EXAMPLES / "nlu_annotation_examples.json").read_text(encoding="utf-8")
)


@pytest.fixture
def payload() -> dict:
    """Return an independent availability fixture without catalogue enrichment."""
    return copy.deepcopy(SAMPLES[0])


def clarify(payload: dict) -> None:
    """Set a schema-only clarification question, without medical instructions."""
    payload["needs_clarification"] = True
    payload["clarification_question"] = {"fr": "Pouvez-vous préciser ?", "ar": None}


@pytest.mark.parametrize("sample", SAMPLES)
def test_sample_payloads_validate_and_round_trip(sample: dict) -> None:
    """All five varieties, voice, directory, clarification and refusal shapes work."""
    model = AnalysisResponse.model_validate(sample)
    dumped = model.model_dump(mode="json")
    assert AnalysisResponse.model_validate_json(model.model_dump_json()) == model
    assert dumped["disclaimer"] == "Cet assistant ne fournit pas de conseil médical."


@pytest.mark.parametrize("value", [-0.1, 1.1, math.nan, math.inf, True, "0.9"])
def test_confidence_rejects_invalid_values(payload: dict, value: object) -> None:
    """Similarity scores must not bypass bounded finite confidence validation."""
    payload["intent"]["confidence"] = value
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize("value", [0, -1, 1.5, "2", True])
def test_quantity_is_an_explicit_positive_integer(payload: dict, value: object) -> None:
    """No coercion of string/bool/fractional/zero counts into valid quantities."""
    payload["input"]["raw_text"] += " 2 boîtes"
    payload["entities"].append(
        {"type": "QUANTITY", "text": "2 boîtes", "value": value, "unit": "box"}
    )
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize("value", [-1, 0.1, "5", True])
def test_latency_requires_nonnegative_integer(payload: dict, value: object) -> None:
    """Elapsed time cannot be negative, a float or silently coerced."""
    payload["latency_ms"] = value
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize("text", ["", " \n\t", "x" * 10001])
def test_invalid_text_input(payload: dict, text: str) -> None:
    """Enforce the public text bounds without altering the raw string."""
    payload["input"]["raw_text"] = text
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize("transcript", [None, "", " \t", "x" * 10001])
def test_voice_requires_valid_transcript(payload: dict, transcript: str | None) -> None:
    """Missing, blank and oversized audio transcripts are invalid."""
    payload["input"].update(modality="voice", raw_text="", transcript=transcript)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "patch",
    [
        {"request_id": "not-a-uuid"},
        {"disclaimer": "Ask me for a dose"},
        {"unknown": "silent field loss is forbidden"},
        {"intent": {"label": "order_medication", "confidence": 0.5}},
        {"intent": {"label": "diagnosis", "confidence": 0.5}},
        {"input": {"modality": "text", "raw_text": "hello", "language": "en"}},
        {"entities": [{"type": "DIAGNOSIS", "text": "Doliprane"}]},
    ],
)
def test_unknown_contract_values_rejected(payload: dict, patch: dict) -> None:
    """Reject unsupported labels and incorrect response contract fields."""
    payload.update(patch)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "entity_patch",
    [
        {"start": 0},
        {"end": 5},
        {"start": -1, "end": 2},
        {"start": 3, "end": 3},
        {"start": True, "end": 4},
        {"start": 0, "end": 9},
        {"text": "invented", "start": None, "end": None},
        {"value": 2},
        {"normalized": "unverified"},
        {"matched_id": "unverified"},
        {"dci": "unverified"},
    ],
)
def test_evidence_and_entity_type_constraints(
    payload: dict, entity_patch: dict
) -> None:
    """Reject invalid offsets, absent evidence and ungrounded identity fields."""
    entity = payload["entities"][0]
    if set(entity_patch) == {"start"}:
        entity.pop("end", None)
    if set(entity_patch) == {"end"}:
        entity.pop("start", None)
    entity.update(entity_patch)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


def test_grounded_identity_shape_does_not_claim_database_verification(
    payload: dict,
) -> None:
    """A matched identity can pass syntax; the future matcher must verify its truth."""
    payload["entities"][0].update(
        normalized="fixture-only", matched_id="test_catalogue_id", dci=None
    )
    assert AnalysisResponse.model_validate(payload).entities[0].matched_id == (
        "test_catalogue_id"
    )


def test_unicode_offsets_use_original_code_points_for_voice_and_text() -> None:
    """Arabic/accents/emoji must not be counted as bytes or UTF-16 code units."""
    payload = copy.deepcopy(SAMPLES[1])
    source = "💬 é واش عندكم دوليبران؟"
    surface = "دوليبران"
    start = source.index(surface)
    payload["input"]["raw_text"] = source
    payload["entities"][0].update(start=start, end=start + len(surface))
    AnalysisResponse.model_validate(payload)
    payload["input"].update(modality="voice", raw_text="", transcript=source)
    AnalysisResponse.model_validate(payload)
    payload["entities"][0]["start"] = len(source[:start].encode("utf-8"))
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "flag,questions",
    [
        (True, {"fr": None, "ar": None}),
        (False, {"fr": "Précisez ?", "ar": None}),
        (True, {"fr": "   ", "ar": None}),
        ("true", {"fr": "Précisez ?", "ar": None}),
    ],
)
def test_clarification_consistency(
    payload: dict, flag: object, questions: dict
) -> None:
    """Flags and actual questions cannot contradict one another."""
    payload.update(needs_clarification=flag, clarification_question=questions)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "intent", ["check_availability", "request_medication", "price_inquiry"]
)
def test_missing_medication_must_clarify(payload: dict, intent: str) -> None:
    """Do not turn an incomplete request into an invented product."""
    payload["intent"]["label"] = intent
    payload["entities"] = []
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    clarify(payload)
    assert AnalysisResponse.model_validate(payload).needs_clarification


@pytest.mark.parametrize("status", ["negated", "uncertain"])
def test_no_affirmed_medication_is_not_an_order(payload: dict, status: str) -> None:
    """Rejected products or alternatives cannot satisfy the active-product check."""
    payload["entities"][0]["assertion"] = status
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    clarify(payload)
    AnalysisResponse.model_validate(payload)


@pytest.mark.parametrize(
    "patch", [{"value": None}, {"unit": None}, {"value": -1}, {"value": "500"}]
)
def test_strength_pair_and_numeric_constraints(payload: dict, patch: dict) -> None:
    """Product strength must have both valid value/unit or remain wholly unresolved."""
    payload["entities"][1].update(patch)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


def test_ambiguous_strength_requires_clarification(payload: dict) -> None:
    """Unparsed product strength is retained verbatim, never guessed."""
    payload["entities"][1].update(value=None, unit=None)
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    clarify(payload)
    assert AnalysisResponse.model_validate(payload).entities[1].value is None


def test_pharmacy_query_requires_primary_intent_and_source_location(
    payload: dict,
) -> None:
    """Directory information must be both intent-consistent and text-grounded."""
    payload["pharmacy_query"].update(needs_pharmacy_info=True, info_type="phone")
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    payload["intent"]["label"] = "pharmacy_info_phone"
    AnalysisResponse.model_validate(payload)
    payload["pharmacy_query"]["location_text"] = "Rabat"
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    payload["input"]["raw_text"] += " à Rabat"
    payload["entities"].append({"type": "LOCATION", "text": "Rabat"})
    AnalysisResponse.model_validate(payload)
    payload["pharmacy_query"]["needs_pharmacy_info"] = False
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


def test_multi_medication_links_and_ambiguity(payload: dict) -> None:
    """Resolve each attribute by mention ID, or keep the request ambiguous."""
    payload["input"]["raw_text"] += " et Panadol"
    payload["entities"][0]["entity_id"] = "med1"
    payload["entities"].append(
        {"type": "MEDICATION", "text": "Panadol", "entity_id": "med2"}
    )
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    clarify(payload)
    AnalysisResponse.model_validate(payload)
    payload["entities"][1]["medication_ref"] = "med1"
    payload.update(
        needs_clarification=False, clarification_question={"fr": None, "ar": None}
    )
    AnalysisResponse.model_validate(payload)
    payload["entities"][1]["medication_ref"] = "absent"
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    payload["entities"][1]["medication_ref"] = "med1"
    payload["entities"][0]["assertion"] = "negated"
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    payload["entities"][0]["assertion"] = "affirmed"
    payload["entities"][2]["entity_id"] = "med1"
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


def test_repeated_mentions_need_distinct_spans(payload: dict) -> None:
    """The same spelling can refer to multiple occurrences without losing offsets."""
    payload["entities"] = [payload["entities"][0]]
    payload["input"]["raw_text"] += " Doliprane"
    second = copy.deepcopy(payload["entities"][0])
    second["start"] = payload["input"]["raw_text"].rindex("Doliprane")
    second["end"] = second["start"] + len("Doliprane")
    payload["entities"].append(second)
    AnalysisResponse.model_validate(payload)


def test_schema_export_is_current_and_cli_is_deterministic(tmp_path: Path) -> None:
    """The checked-in schema is generated, not hand-maintained independently."""
    expected = AnalysisResponse.model_json_schema()
    assert json.loads((ROOT / "docs/response_v1.schema.json").read_text()) == expected
    output = tmp_path / "nested" / "schema.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/export_schema.py"),
            "--output",
            str(output),
        ],
        check=True,
        cwd=tmp_path,
        capture_output=True,
    )
    assert json.loads(output.read_text()) == expected


def test_annotation_coverage_and_provenance() -> None:
    """Check the exact 8x5x5 coverage, unique IDs and unreviewed provenance."""
    intents = {
        "check_availability",
        "request_medication",
        "pharmacy_info_phone",
        "pharmacy_info_location",
        "pharmacy_info_hours",
        "price_inquiry",
        "greeting_smalltalk",
        "out_of_scope",
    }
    languages = {"darija_ar", "darija_latn", "ar", "fr", "mixed"}
    counts = Counter((row["intent"], row["language"]) for row in ANNOTATIONS)
    assert set(counts) == {(intent, lang) for intent in intents for lang in languages}
    assert all(count == 5 for count in counts.values())
    assert len({row["id"] for row in ANNOTATIONS}) == 200
    assert all(row["source"] == "authored_unreviewed" for row in ANNOTATIONS)
    assert all(
        row["review_status"] == "pending_native_speaker_review" for row in ANNOTATIONS
    )


@pytest.mark.parametrize("row", ANNOTATIONS, ids=lambda row: row["id"])
def test_annotation_spans_and_contract(row: dict) -> None:
    """Every authored annotation must select real text and satisfy the contract."""
    adapter = TypeAdapter(Entity)
    for entity in row["entities"]:
        adapter.validate_python(entity)
        assert row["text"][entity["start"] : entity["end"]] == entity["text"]
    payload = copy.deepcopy(SAMPLES[0])
    payload["input"].update(raw_text=row["text"], language=row["language"])
    payload["entities"] = row["entities"]
    payload["intent"]["label"] = row["intent"]
    info = {
        "pharmacy_info_phone": "phone",
        "pharmacy_info_location": "location",
        "pharmacy_info_hours": "hours",
    }.get(row["intent"])
    payload["pharmacy_query"].update(
        needs_pharmacy_info=info is not None, info_type=info
    )
    if row["needs_clarification"]:
        clarify(payload)
    AnalysisResponse.model_validate(payload)


def test_repeated_entities_reject_duplicate_or_missing_offsets(payload: dict) -> None:
    """Reject duplicated occurrences and unlocated repeated mentions."""
    payload["entities"] = [
        payload["entities"][0],
        copy.deepcopy(payload["entities"][0]),
    ]
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)
    payload["entities"][1].pop("start")
    payload["entities"][1].pop("end")
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(payload)


def test_out_of_scope_does_not_ask_for_medical_attribute_clarification(
    payload: dict,
) -> None:
    """A refusal may retain ambiguous evidence without dosage clarification."""
    payload["intent"]["label"] = "out_of_scope"
    payload["entities"][0]["assertion"] = "uncertain"
    payload["entities"][1].update(value=None, unit=None)
    result = AnalysisResponse.model_validate(payload)
    assert not result.needs_clarification


def test_other_entity_variants_validate_verbatim(payload: dict) -> None:
    """Exercise form, pharmacy, time and urgency variants beyond medication/counts."""
    source = (
        "Avez-vous Doliprane en sirop à la Pharmacie Exemple à Rabat ce soir, urgent ?"
    )
    payload["input"]["raw_text"] = source
    payload["entities"] = [
        {"type": "MEDICATION", "text": "Doliprane"},
        {"type": "FORM", "text": "sirop", "normalized": "syrup"},
        {"type": "PHARMACY_NAME", "text": "Pharmacie Exemple"},
        {"type": "LOCATION", "text": "Rabat"},
        {"type": "TIME_REF", "text": "ce soir", "normalized": "tonight"},
        {"type": "URGENCY", "text": "urgent", "normalized": "urgent"},
    ]
    assert len(AnalysisResponse.model_validate(payload).entities) == 6


def test_corrected_request_keeps_rejected_and_affirmed_mentions(payload: dict) -> None:
    """Negation marks the rejected name without losing the active request."""
    payload["input"]["raw_text"] = "Pas Doliprane, Panadol"
    payload["intent"]["label"] = "request_medication"
    payload["entities"] = [
        {"type": "MEDICATION", "text": "Doliprane", "assertion": "negated"},
        {"type": "MEDICATION", "text": "Panadol", "assertion": "affirmed"},
    ]
    result = AnalysisResponse.model_validate(payload)
    assert [entity.assertion for entity in result.entities] == ["negated", "affirmed"]
