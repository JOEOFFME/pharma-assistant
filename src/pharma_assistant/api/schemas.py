"""Version-one NLU contracts; validation checks structure, not medication truth."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonBlank = Annotated[str, StringConstraints(pattern=r"\S")]
Score = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
PositiveNumber = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
Offset = Annotated[int, Field(strict=True, ge=0)]
Language = Literal["darija_ar", "darija_latn", "ar", "fr", "mixed"]
IntentLabel = Literal[
    "check_availability",
    "request_medication",
    "pharmacy_info_phone",
    "pharmacy_info_location",
    "pharmacy_info_hours",
    "price_inquiry",
    "greeting_smalltalk",
    "out_of_scope",
]
DISCLAIMER = "Cet assistant ne fournit pas de conseil médical."


class ContractModel(BaseModel):
    """Reject misspelled/unknown fields rather than silently dropping them."""

    model_config = ConfigDict(extra="forbid", validate_default=True)


class InputInfo(ContractModel):
    """Preserve raw text; offsets for voice refer to the transcript."""

    modality: Literal["text", "voice"]
    raw_text: str = Field(max_length=10000)
    transcript: Annotated[NonBlank, Field(max_length=10000)] | None = None
    language: Language

    @model_validator(mode="after")
    def validate_modality(self) -> Self:
        """Text needs nonblank raw input; voice needs a nonblank transcript."""
        if self.modality == "text":
            if not self.raw_text.strip() or self.transcript is not None:
                raise ValueError("Text requires nonblank raw_text and null transcript")
        elif self.transcript is None:
            raise ValueError("Voice requires a transcript")
        return self


class Intent(ContractModel):
    """Confidence must be an explicitly supplied bounded score."""

    label: IntentLabel
    confidence: Score


class EntityBase(ContractModel):
    """Surface evidence, optional raw offsets and explicit assertion status."""

    text: NonBlank
    start: Offset | None = None
    end: Offset | None = None
    entity_id: NonBlank | None = None
    assertion: Literal["affirmed", "negated", "uncertain"] = "affirmed"
    confidence: Score | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> Self:
        """Offsets must be supplied together as a nonempty half-open interval."""
        if (self.start is None) != (self.end is None):
            raise ValueError("Provide both start and end, or neither")
        if self.start is not None and self.end is not None and self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class MedicationEntity(EntityBase):
    """Only catalogue-grounded matches may carry normalized identity fields."""

    type: Literal["MEDICATION"]
    normalized: NonBlank | None = None
    dci: NonBlank | None = None
    matched_id: NonBlank | None = None

    @model_validator(mode="after")
    def validate_resolution(self) -> Self:
        """Require a reference identity for normalized names and ingredients."""
        if (self.normalized is None) != (self.matched_id is None):
            raise ValueError("normalized and matched_id must be supplied together")
        if self.dci is not None and self.matched_id is None:
            raise ValueError("dci requires a catalogue match")
        return self


class MedicationAttribute(EntityBase):
    """Optional association to a MEDICATION entity_id, not a catalogue ID."""

    medication_ref: NonBlank | None = None


class DosageEntity(MedicationAttribute):
    """Extract stated product strength; never recommend a dose or regimen."""

    type: Literal["DOSAGE"]
    value: PositiveNumber | None = None
    unit: Literal["mg", "g", "mcg", "mg/mL", "g/L", "%", "IU"] | None = None

    @model_validator(mode="after")
    def validate_value_unit(self) -> Self:
        """Ambiguous/compound strengths remain raw with both fields null."""
        if (self.value is None) != (self.unit is None):
            raise ValueError("Provide both value and unit, or neither")
        return self


class FormEntity(MedicationAttribute):
    """Product form as stated, with an optional controlled normalization."""

    type: Literal["FORM"]
    normalized: (
        Literal[
            "tablet",
            "capsule",
            "syrup",
            "suspension",
            "injection",
            "cream",
            "ointment",
            "drops",
            "spray",
            "suppository",
            "sachet",
            "powder",
            "other",
        ]
        | None
    ) = None


class QuantityEntity(MedicationAttribute):
    """Explicit positive count of requested packages or discrete units."""

    type: Literal["QUANTITY"]
    value: Annotated[int, Field(strict=True, gt=0)]
    unit: Literal[
        "box",
        "blister",
        "bottle",
        "tablet",
        "tube",
        "sachet",
        "ampoule",
        "vial",
        "pack",
        "unit",
    ]


class PharmacyNameEntity(EntityBase):
    """Pharmacy name as mentioned; no implied directory match."""

    type: Literal["PHARMACY_NAME"]
    normalized: NonBlank | None = None


class LocationEntity(EntityBase):
    """Location text; does not pretend to be geocoded coordinates."""

    type: Literal["LOCATION"]
    normalized: NonBlank | None = None


class TimeRefEntity(EntityBase):
    """Relative/absolute time text; resolution requires request-time context."""

    type: Literal["TIME_REF"]
    normalized: Literal["today", "tonight", "now", "tomorrow"] | None = None


class UrgencyEntity(EntityBase):
    """Explicit request urgency, without inferring clinical severity."""

    type: Literal["URGENCY"]
    normalized: Literal["urgent"] | None = None


Entity = Annotated[
    MedicationEntity
    | DosageEntity
    | FormEntity
    | QuantityEntity
    | PharmacyNameEntity
    | LocationEntity
    | TimeRefEntity
    | UrgencyEntity,
    Field(discriminator="type"),
]


class PharmacyQuery(ContractModel):
    """Describe a directory-information request, not an answer or stock check."""

    needs_pharmacy_info: Annotated[bool, Field(strict=True)]
    info_type: Literal["phone", "location", "hours"] | None = None
    location_text: NonBlank | None = None

    @model_validator(mode="after")
    def validate_info_type(self) -> Self:
        """Directory flags must agree, and inactive queries carry no location."""
        if self.needs_pharmacy_info != (self.info_type is not None):
            raise ValueError("needs_pharmacy_info must agree with info_type")
        if not self.needs_pharmacy_info and self.location_text is not None:
            raise ValueError("Inactive pharmacy query cannot carry location_text")
        return self


class ClarificationQuestion(ContractModel):
    """Questions in supported response languages; absent values are null."""

    fr: NonBlank | None = None
    ar: NonBlank | None = None


class Relation(ContractModel):
    """Directed mention association; IDs refer to spans, never catalogue IDs."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["QUANTITY_OF", "DOSAGE_OF"]
    from_id: NonBlank = Field(alias="from")
    to: NonBlank


class AnalysisResponse(ContractModel):
    """Structured interpretation v1 with cross-field consistency checks."""

    request_id: UUID
    input: InputInfo
    intent: Intent
    entities: list[Entity]
    relations: list[Relation] = Field(default_factory=list)
    contains_out_of_scope_request: Annotated[bool, Field(strict=True)] = False
    pharmacy_query: PharmacyQuery
    needs_clarification: Annotated[bool, Field(strict=True)]
    clarification_question: ClarificationQuestion
    disclaimer: Literal["Cet assistant ne fournit pas de conseil médical."] = DISCLAIMER
    latency_ms: Annotated[int, Field(strict=True, ge=0)]

    @model_validator(mode="after")
    def validate_interpretation(self) -> Self:
        """Check evidence alignment, entity links and clarification obligations."""
        question = self.clarification_question
        if self.needs_clarification != (
            question.fr is not None or question.ar is not None
        ):
            raise ValueError("Clarification flag must agree with question presence")
        directory_intents = {
            "pharmacy_info_phone": "phone",
            "pharmacy_info_location": "location",
            "pharmacy_info_hours": "hours",
        }
        expected = directory_intents.get(self.intent.label)
        if self.pharmacy_query.info_type != expected:
            raise ValueError("pharmacy_query must agree with the primary intent")
        source = (
            self.input.transcript
            if self.input.modality == "voice"
            else self.input.raw_text
        )
        assert source is not None  # InputInfo has already validated the modality.
        ids = [
            entity.entity_id for entity in self.entities if entity.entity_id is not None
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("entity_id values must be unique")
        medications = {
            entity.entity_id: entity
            for entity in self.entities
            if isinstance(entity, MedicationEntity) and entity.entity_id is not None
        }
        affirmed_meds = [
            entity
            for entity in self.entities
            if isinstance(entity, MedicationEntity) and entity.assertion == "affirmed"
        ]
        located = sorted(
            (entity for entity in self.entities if entity.start is not None),
            key=lambda entity: entity.start,
        )
        if any(
            left.end > right.start
            for left, right in zip(located, located[1:], strict=False)
        ):
            raise ValueError("Overlapping entity spans")
        by_id = {
            entity.entity_id: entity for entity in self.entities if entity.entity_id
        }
        seen_relations = set()
        for relation in self.relations:
            key = (relation.type, relation.from_id, relation.to)
            if key in seen_relations:
                raise ValueError("Duplicate relation")
            seen_relations.add(key)
            attribute = by_id.get(relation.from_id)
            target = by_id.get(relation.to)
            expected_type = {"QUANTITY_OF": "QUANTITY", "DOSAGE_OF": "DOSAGE"}[
                relation.type
            ]
            if (
                attribute is None
                or attribute.type != expected_type
                or not isinstance(target, MedicationEntity)
            ):
                raise ValueError(
                    "Relation endpoints must have the correct entity types"
                )
            if (
                attribute.medication_ref is not None
                and attribute.medication_ref != relation.to
            ):
                raise ValueError("Relation conflicts with medication_ref")
            if attribute.assertion == "affirmed" and target.assertion != "affirmed":
                raise ValueError(
                    "Affirmed relation cannot target a rejected medication"
                )
        location_text = self.pharmacy_query.location_text
        if location_text is not None and not any(
            isinstance(entity, LocationEntity)
            and entity.text == location_text
            and entity.assertion == "affirmed"
            for entity in self.entities
        ):
            raise ValueError("location_text must be an affirmed LOCATION mention")
        occurrences: dict[tuple[str, str], list[EntityBase]] = {}
        for entity in self.entities:
            occurrences.setdefault((entity.type, entity.text), []).append(entity)
        for mentions in occurrences.values():
            if len(mentions) > 1:
                positions = {(mention.start, mention.end) for mention in mentions}
                if any(mention.start is None for mention in mentions) or len(
                    positions
                ) != len(mentions):
                    raise ValueError(
                        "Repeated entity mentions need distinct explicit offsets"
                    )
        for entity in self.entities:
            if (
                entity.assertion == "uncertain"
                and self.intent.label != "out_of_scope"
                and not self.needs_clarification
            ):
                raise ValueError("Uncertain entities require clarification")
            if entity.text not in source:
                raise ValueError("Entity text must occur verbatim in the source")
            if (
                entity.start is not None
                and source[entity.start : entity.end] != entity.text
            ):
                raise ValueError("Entity offsets must select the exact original text")
            if isinstance(entity, MedicationAttribute):
                ref = entity.medication_ref
                if ref is not None:
                    if ref not in medications:
                        raise ValueError(
                            "medication_ref must point to a MEDICATION entity"
                        )
                    target = medications[ref]
                    if (
                        entity.assertion == "affirmed"
                        and target.assertion != "affirmed"
                    ):
                        raise ValueError(
                            "Affirmed attribute cannot target a negated/uncertain med"
                        )
                if (
                    entity.assertion == "affirmed"
                    and self.intent.label != "out_of_scope"
                    and len(affirmed_meds) > 1
                    and ref is None
                    and not any(r.from_id == entity.entity_id for r in self.relations)
                    and not self.needs_clarification
                ):
                    raise ValueError(
                        "Multi-medication attributes need links or clarification"
                    )
            if (
                isinstance(entity, DosageEntity)
                and entity.assertion != "negated"
                and self.intent.label != "out_of_scope"
                and entity.value is None
                and not self.needs_clarification
            ):
                raise ValueError("Unparsed strength requires clarification")
        if (
            self.intent.label
            in {"request_medication", "check_availability", "price_inquiry"}
            and not affirmed_meds
            and not self.needs_clarification
        ):
            raise ValueError(
                "Medication intent without an affirmed medication must clarify"
            )
        return self


class NLUAnnotation(ContractModel):
    """Versioned annotation record; creation provenance never implies verification."""

    id: NonBlank
    text: Annotated[NonBlank, Field(max_length=10000)]
    language: Language
    intent: IntentLabel
    entities: list[Entity]
    relations: list[Relation]
    needs_clarification: Annotated[bool, Field(strict=True)]
    contains_out_of_scope_request: Annotated[bool, Field(strict=True)]
    source: Literal["assistant_seed", "synthetic", "llm", "human"]
    verified: Annotated[bool, Field(strict=True)]
    family_id: NonBlank
    split: NonBlank
    authoring_method: str | None = None
    expected_action: str | None = None
    review_status: str | None = None
    source_example_id: str | None = None
    parent_id: str | None = None
    augmentation: dict | None = None

    @model_validator(mode="after")
    def validate_annotation(self) -> Self:
        """Apply the response evidence rules without inventing predicted scores."""
        if self.verified and self.source != "human":
            raise ValueError("Only human annotations may be verified")
        if self.source == "synthetic" and not self.parent_id:
            raise ValueError("Synthetic examples require a parent")
        if any(e.start is None or e.entity_id is None for e in self.entities):
            raise ValueError("Annotations require offsets and unique span IDs")
        info = {
            "pharmacy_info_phone": "phone",
            "pharmacy_info_location": "location",
            "pharmacy_info_hours": "hours",
        }.get(self.intent)
        AnalysisResponse.model_validate(
            {
                "request_id": "00000000-0000-4000-8000-000000000001",
                "input": {
                    "modality": "text",
                    "raw_text": self.text,
                    "language": self.language,
                },
                "intent": {"label": self.intent, "confidence": 0.5},
                "entities": [e.model_dump(exclude_none=True) for e in self.entities],
                "relations": [r.model_dump(by_alias=True) for r in self.relations],
                "contains_out_of_scope_request": self.contains_out_of_scope_request,
                "pharmacy_query": {
                    "needs_pharmacy_info": info is not None,
                    "info_type": info,
                },
                "needs_clarification": self.needs_clarification,
                "clarification_question": {
                    "fr": "Pouvez-vous préciser ?" if self.needs_clarification else None
                },
                "latency_ms": 0,
            }
        )
        return self
