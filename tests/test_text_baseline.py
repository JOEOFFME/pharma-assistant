"""Normalizer, heuristic and end-to-end baseline contracts with real source records."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pharma_assistant.api.schemas import AnalysisResponse
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.eval.text_baseline import evaluate, metrics
from pharma_assistant.nlp.intent import classify_intent
from pharma_assistant.nlp.langid import detect_language
from pharma_assistant.nlp.normalize import normalize
from pharma_assistant.pipeline.text_pipeline import TextPipeline

ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config(ROOT / "configs/baseline.yaml")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  École!!!  ", "ecole"),
        ("أَإِآـى", "ااي"),
        ("ﻻ", "لا"),
        ("coooool", "cool"),
        ("boîtes", "boites"),
        ("٥٠٠ mg", "500 mg"),
        ("3afak 7ebba 9alb 1000mg", "عafak حebba قalb 1000mg"),
        ("500 mg 1000 1g", "500 mg 1000 1g"),
        ("🙂", ""),
    ],
)
def test_normalization_components(raw: str, expected: str) -> None:
    """Fold Unicode, accents, Arabic, punctuation/repeats and lexical digits only."""
    result = normalize(raw)
    assert result.text == expected
    assert len(result.spans) == len(expected)
    assert all(0 <= start < end <= len(raw) for start, end in result.spans)


def test_alignment_survives_marks_emoji_and_repetitions() -> None:
    """Normalized offsets identify original spelling, using Unicode code points."""
    raw = "🙂 ÉÉÉ, دُولِيبْران!"
    folded = normalize(raw)
    start = folded.text.index("دوليبران")
    a, b = folded.original_span(start, start + len("دوليبران"))
    assert raw[a:b] == "دُولِيبْران"
    a, b = folded.original_span(0, 2)
    assert raw[a:b] == "ÉÉÉ"
    with pytest.raises(ValueError):
        folded.original_span(1, 1)


@pytest.mark.parametrize(
    "text,language",
    [
        ("واش كاين Doliprane 500 mg؟", "darija_ar"),
        ("هل يتوفر لديكم دوليبران؟", "ar"),
        ("wach kayn Doliprane?", "darija_latn"),
        ("Bonjour, vous avez Doliprane ?", "fr"),
        ("واش vous avez le sirop?", "mixed"),
        ("bghit le prix", "mixed"),
    ],
)
def test_language_script_and_lexical_signals(text: str, language: str) -> None:
    """A Latin medication/unit alone does not turn Arabic/Darija into mixed."""
    assert detect_language(text) == language


@pytest.mark.parametrize(
    "text,label,mixed",
    [
        ("Je voudrais Doliprane", "request_medication", False),
        ("Je voudrais connaître le prix de Doliprane", "price_inquiry", False),
        ("واش كاين دوليبران؟", "check_availability", False),
        ("Doliprane kayn? ch7al men 7ebba nakhod?", "check_availability", True),
        ("Quelle dose de Doliprane pour un enfant ?", "out_of_scope", False),
        ("Je peux remplacer Augmentin ?", "out_of_scope", False),
        ("شنو نمرة الصيدلية؟", "pharmacy_info_phone", False),
        ("Bonjour", "greeting_smalltalk", False),
    ],
)
def test_intent_rules_and_medical_advice_boundary(
    text: str, label: str, mixed: bool
) -> None:
    """Supported requests retain routing while pure medical advice is refused."""
    actual, flag, _ = classify_intent(text, CONFIG)
    assert (actual, flag) == (label, mixed)


@pytest.mark.parametrize(
    "text",
    [
        "🙂 Avez-vous Doliprane 500 mg en sirop ?",
        "بغيت 2 علب ديال دوليبران",
        "Je voudrais 2 boîtes de Doliprane et 1 boîte de Spasfon",
        "Pas Doliprane, Spasfon",
        "Je voudrais Doliprane ou Spasfon",
        "Pharmacie de garde à Rabat ce soir ?",
        "Numéro de Pharmacie Exemple à Rabat ?",
        "Je voudrais Doliprane 875/125 mg",
        "Je voudrais Doliprane 0 mg",
        "Je voudrais 1.5 boîtes de Doliprane",
    ],
)
def test_pipeline_schema_original_evidence_and_associations(
    pipeline: TextPipeline, text: str
) -> None:
    """Full v1 results preserve raw evidence and the required disclaimer."""
    result = pipeline.analyze(text)
    assert (
        AnalysisResponse.model_validate_json(result.model_dump_json(by_alias=True))
        == result
    )
    assert result.input.raw_text == text
    assert result.disclaimer == "Cet assistant ne fournit pas de conseil médical."
    for e in result.entities:
        assert text[e.start : e.end] == e.text
    if "875/125" in text:
        assert result.needs_clarification
        assert (
            next(e for e in result.entities if e.type == "DOSAGE").text == "875/125 mg"
        )
    if "1.5" in text:
        assert not any(e.type == "QUANTITY" for e in result.entities)
    if "Pas" in text:
        assert (
            next(e for e in result.entities if e.type == "MEDICATION").assertion
            == "negated"
        )


def test_missing_medication_and_unknown_language(pipeline: TextPipeline) -> None:
    """Incomplete requests clarify; invalid hints/text fail before extraction."""
    result = pipeline.analyze("Je voudrais 2 boîtes", language_hint="fr")
    assert result.intent.label == "request_medication" and result.needs_clarification
    for text in ["", " ", "a" * 10001, None]:
        with pytest.raises(ValidationError):
            pipeline.analyze(text)
    with pytest.raises(ValidationError):
        pipeline.analyze("bonjour", language_hint="en")


def test_live_index_resolution_and_strength_ambiguity(pipeline: TextPipeline) -> None:
    """Resolution uses index records and retains explicit strength ambiguity."""
    resolved = pipeline.analyze("Je voudrais Spasfon")
    meds = [e for e in resolved.entities if e.type == "MEDICATION"]
    assert meds and meds[0].matched_id in pipeline.extractor.index.records
    ambiguous = pipeline.analyze("Vous avez Doliprane 500 ?")
    assert ambiguous.needs_clarification
    dosage = next(e for e in ambiguous.entities if e.type == "DOSAGE")
    assert dosage.value is None and dosage.unit is None


def test_evaluation_known_counts_and_alignment() -> None:
    """Metrics are validated against hand-counted TP/FP/FN, including wrong ordering."""
    rows = [
        {
            "text": "a",
            "intent": "check_availability",
            "entities": [{"type": "MEDICATION", "start": 0, "end": 1}],
        }
    ]
    predictions = [
        {
            "input": {"raw_text": "a"},
            "intent": {"label": "check_availability"},
            "entities": [
                {"type": "MEDICATION", "start": 0, "end": 1},
                {"type": "FORM", "start": 0, "end": 1},
            ],
        }
    ]
    result = metrics(rows, predictions)
    assert result["intent_accuracy"] == 1
    assert result["intent_macro_f1"] == 1 / 8
    assert result["entity_exact_micro"]["f1"] == pytest.approx(2 / 3)
    predictions[0]["input"]["raw_text"] = "wrong"
    with pytest.raises(ValueError, match="aligned"):
        metrics(rows, predictions)


def test_evaluation_rejects_empty_or_unverified_human_gold(
    pipeline: TextPipeline, tmp_path: Path
) -> None:
    """No gold metric is fabricated from an empty file or automatic annotations."""
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    with pytest.raises(ValueError, match="empty"):
        evaluate(pipeline, empty, tmp_path / "result.json", cohort="human_gold")
    with pytest.raises(ValueError, match="verified human"):
        evaluate(
            pipeline,
            ROOT / "data/nlu/gold_review.jsonl",
            tmp_path / "result.json",
            cohort="human_gold",
        )
