# NLU specification and annotation guidelines - v1

TASK 2 specification, amended during TASK 5 at the user’s request. Version: v1.
This defines a request interpretation contract, not medication facts or medical
advice. The pipeline and analysis endpoints are later tasks.

## 1. Scope and taxonomy

Use one primary intent for each complete message. `request_medication` is the
canonical label: `order_medication` is a documentation synonym, not a valid wire
label. An order/request label records what was said; it never confirms a sale,
stock, prescription validity, fulfillment or authorization to dispense.

| Label | Include | Exclude / boundary |
| --- | --- | --- |
| `check_availability` | Whether a named/referred product exists in the pharmacy's stock. | Product price alone; asking when a pharmacy opens. |
| `request_medication` | Explicit desire to obtain/request a product or package. | `Je voudrais connaître le prix` is a price question, not a purchase request. |
| `pharmacy_info_phone` | Phone/contact number of a pharmacy. | Requesting a product, even if it mentions a pharmacy. |
| `pharmacy_info_location` | Address, directions or nearest pharmacy. | A pharmacy's hours/on-duty schedule. |
| `pharmacy_info_hours` | Opening/closing time, open now, or on-duty pharmacy. | Availability of a medication. Never infer live garde status from a static directory. |
| `price_inquiry` | Cost/price of a medication/presentation. | Medical benefit or dosage question. |
| `greeting_smalltalk` | Greeting, thanks or brief social exchange with no substantive task. | Greeting followed by a substantive request: use that request's label. |
| `out_of_scope` | Medical diagnosis, dose/regimen recommendation, substitution advice, unrelated requests or unintelligible input with no recoverable supported request. | Incomplete but recognizable pharmacy requests: retain their intent and clarify. |

### Primary-intent decision procedure

1. When an in-scope request and an out-of-scope request occur together, retain
   the **in-scope primary intent** and set `contains_out_of_scope_request=true`.
   For `Doliprane kayn? o golo lia ch7al men 7ebba nakhod`, use
   `check_availability`. Answer the in-scope part within available evidence
   (never invent live stock); politely refuse the medical-advice part. Only
   messages with no supported request use `out_of_scope`. This flag records an
   additional unsupported request; it does not authorize advice.
2. Otherwise identify the actual requested action, not isolated keywords.
   `Je voudrais savoir si X est disponible` is availability; `bghit n3ref prix X`
   is price; `Je voudrais X` is a medication request.
3. If multiple independent supported actions remain, choose the first present
   in this fixed priority: request_medication > check_availability >
   price_inquiry > pharmacy_info_location > pharmacy_info_hours >
   pharmacy_info_phone > greeting_smalltalk. Set clarification true to ask which
   action to handle first. Do not silently claim all actions are handled.
4. Fallback to `out_of_scope` for unrelated/irrecoverable input. A missing
   medication does not erase a recognizable availability or request intent.

V1 has no secondary-intent array. Additional clauses remain available in raw
text; the single `pharmacy_query` corresponds only to the primary intent.
An out-of-scope label is a routing decision; a later API response layer must
supply a fixed refusal/redirect, without executing medical recommendations.
The schema alone cannot determine whether a sentence constitutes medical advice.

## 2. Entity inventory and boundaries

Offsets are half-open `[start, end)` indices into the **original raw_text** for
text input and the **transcript** for voice input. Count Python/Unicode code
points, not UTF-8 bytes, JavaScript UTF-16 code units, tokens or screen columns.
Preserve accents, Arabic marks and punctuation in the underlying string. Do not
normalize it before computing spans. Store a normalization alignment map in the
future pipeline. Annotation records must include start/end; the public response
also accepts both omitted for compatibility with the original AGENTS example.

Use minimal contiguous spans covering the actual entity. Exclude surrounding
prepositions, question marks and unrelated words. Exclude attached clitic
prefixes `ف`, `ل`, `ب`, `و`, `l'`, `d'` when they function as prefixes,
not when a letter belongs to the real entity name. Include the number and unit
for quantities/strengths. One mention per occurrence, with offsets mandatory
when the same surface repeats. Do not create an entity from an inferred word.

| Type | Span rule | Structured fields / limits |
| --- | --- | --- |
| `MEDICATION` | User's product/ingredient name alone; exclude strength and form. Pronouns such as `هاد الدوا` are unresolved references, not names. | `normalized`, `matched_id`, `dci` default null. Only a verified catalogue match may populate identity; normalized and matched_id must occur together, DCI needs a match. |
| `DOSAGE` | User-stated **product strength**, e.g. `500 mg`; the legacy field name does not permit dosage advice. | Positive finite value and unit together, or both null for ambiguous/compound expressions. Units: mg, g, mcg, mg/mL, g/L, %, IU. Preserve original unit text, use canonical case. Do not convert units in v1. |
| `FORM` | Stated physical form, e.g. `sirop`, `comprimés`; exclude packaging. | Optional normalized: tablet, capsule, syrup, suspension, injection, cream, ointment, drops, spray, suppository, sachet, powder, other. `other` means known but outside this vocabulary; null means unresolved. |
| `QUANTITY` | Explicit count plus package/discrete-unit phrase, e.g. `2 boîtes`, `علبتين`. | Positive integer value; units: box, blister, bottle, tablet, tube, sachet, ampoule, vial, pack, unit. `unit` is an explicit count lacking a more specific unit, not an inferred box. No zero, fractional, negative or string count. |
| `PHARMACY_NAME` | Proper pharmacy name only. Exclude generic `صيدلية` / `Pharmacie` unless evidence establishes that the word is part of the real name. Generic `la pharmacie` alone is not a name. | Optional normalized directory name, no invented contact information. |
| `LOCATION` | Explicit city/neighborhood/street/address mention; `près de moi` is relative, not a fabricated coordinate. | Optional normalized label. Geocoding is separate. |
| `TIME_REF` | Full explicit time expression, e.g. `daba`, `ce soir`, `had lila`, `الليلة`, `هذه الليلة`; never annotate only `lila` inside `had lila`. | Optional now/today/tonight/tomorrow; other expressions stay raw. Exact dates require request timestamp/timezone in a later component. |
| `URGENCY` | Explicit urgency phrase, e.g. `urgent`, `ضروري دابا`. | Optional normalized urgent. Never infer clinical severity or emergency diagnosis. |

All entities include `text`, optional paired offsets, optional `entity_id`,
`assertion` (affirmed by default, negated, uncertain), and optional bounded
confidence. Normalized values are not allowed to replace the verbatim text.
Arbitrary explanatory fields are rejected (`extra=forbid`).

### Association and repetition

JSONL annotations include a `relations` list. Each entity has a unique
`entity_id`; links use those mention IDs:
`{"type":"QUANTITY_OF","from":"q1","to":"med1"}` and
`{"type":"DOSAGE_OF","from":"d1","to":"med1"}`.
Quantity/strength relations must start at the corresponding entity type and end
at a MEDICATION. Duplicate, dangling, mistyped and contradictory links are
rejected. If `medication_ref` is also supplied, it must agree with the relation.
Do not infer a relationship when genuinely ambiguous; clarify instead.


For multiple medications, give each MEDICATION occurrence a unique `entity_id`
(e.g. med1, med2). DOSAGE, FORM and QUANTITY may point to the corresponding
`entity_id` through `medication_ref`. This is a within-response mention link,
not a catalogue matched_id. Repeated mentions of one product have different IDs;
a catalogue match may share the same matched_id. Do not merge unresolved spans.

If association is genuinely ambiguous for a supported request, leave medication_ref
null and request clarification. Out-of-scope messages are routed for refusal and
do not need clarification to resolve product attributes. For in-scope intents, multiple affirmed medications with any unlinked affirmed
attributes are rejected unless clarification is true. A supplied link must
resolve to a MEDICATION entity; an affirmed attribute cannot target a negated or
uncertain medication. For one medication, the link is optional. Attributes may
exist with no named medication if the response asks for that missing name.

## 3. Annotation procedure

1. Keep the message exactly as authored/recorded. Verify UTF-8 and retain a
   stable example ID. Do not fix typos in the source field.
2. Assign language: darija_ar for Darija with Arabic-script lexical content;
   darija_latn for Latin Darija/Arabizi; ar for MSA; fr for French; mixed for
   clauses/phrases from multiple varieties. A Latin brand, strength unit or
   isolated conventional borrowing alone does not force mixed. Script alone
   does not distinguish MSA and Darija. Ambiguous greetings use their intended
   collection context, with reviewer notes rather than fabricated certainty.
3. Apply the intent decision procedure. Annotate spans in the original message.
   Use negated for explicitly rejected entities and uncertain for unresolved
   alternatives. Do not silently promote an alternative to affirmed.
4. Normalize only explicit quantities, units, forms and unambiguous relative time.
   Interpret Arabizi numerals in lexical tokens, never globally: `3afak` and
   `500 mg` require different handling. Preserve source offsets regardless.
5. Resolve medication names only against the approved reference dataset. Without
   it, leave normalized/matched_id/DCI null. Author examples in this task have no
   catalogue enrichment. Spelling resemblance cannot establish active ingredient.
6. Mark clarification needs, including missing medication, ambiguous strength or
   association, unresolved alternatives, missing directory identity/location and
   multiple independent actions. A missing package count alone is not an error:
   keep it unspecified and do not default to one.
7. A native-speaker annotator reviews text, variety, intent, spans and relations;
   a second reviewer adjudicates disagreements before gold-set promotion. Record
   reviewer IDs, revision and adjudication notes in TASK 5. No example here has
   completed that review.

The later dataset task must split by template family and group translations and
paraphrases from the same seed. TASK 2 examples are a specification aid, not a
held-out evaluation set. Never promote them to gold solely because they validate.

## 4. Clarification, negation and hard cases

| Case | Rule / expected result |
| --- | --- |
| `Bonjour, avez-vous Doliprane ?` | check_availability; greeting is subordinate. |
| `Je voudrais connaître le prix de Doliprane` | price_inquiry; `voudrais` alone is insufficient for a purchase label. |
| `Je voudrais 2 boîtes` | request_medication, explicit quantity, no MEDICATION, clarification asks which product. |
| `Je voudrais Doliprane` | request_medication, medication only; absent quantity is unspecified, no automatic clarification solely for that omission. |
| `Pas Doliprane, Panadol` | Context-free elliptical medication request: mark Doliprane negated, Panadol affirmed; quantities are not inferred. Review conversational context if available. |
| `Je voudrais Doliprane ou Panadol` | Both medication mentions uncertain; clarify which product. No catalogue substitution claim. |
| `Je voudrais 2 boîtes de Doliprane et 1 boîte de Panadol` | Two affirmed medications, two distinct quantity spans, explicit mention links. |
| `Je voudrais Doliprane et Panadol, 2 boîtes` | Two affirmed medications; quantity is unlinked and needs clarification about association. |
| `Avez-vous Doliprane 500 ?` | DOSAGE text `500`, value/unit null because strength unit is absent; clarify, do not infer mg. |
| `Avez-vous X 875/125 mg ?` | MEDICATION text `X`, compound DOSAGE text `875/125 mg`, value/unit null; clarify rather than collapsing to one scalar. No claim that X is a real medicine. |
| `Je voudrais 2 boîtes de Doliprane 500 mg en comprimés` | Separate quantity, medication, strength and FORM; `comprimés` is form here, not a second quantity. |
| `Je voudrais 2 comprimés de Doliprane` | QUANTITY is `2 comprimés`, unit tablet; avoid an overlapping duplicate FORM on the same head noun. |
| `Je voudrais zéro boîte finalement` | Cancelled request; no positive quantity entity. Keep recognizable request intent, clarify cancellation/desired action. Never turn zero into one. |
| `Avez-vous Doliprane et combien dois-je en prendre ?` | check_availability with contains_out_of_scope_request=true; handle availability and politely refuse the dosing-advice clause. |
| `Numéro de la pharmacie ?` | pharmacy_info_phone; context-free directory target missing, clarify pharmacy name or city. |
| `Pharmacie de garde ce soir ?` | pharmacy_info_hours, TIME_REF; clarify location if absent; no invented duty roster. |
| `Adresse et téléphone de la pharmacie à Rabat ?` | Primary pharmacy_info_location, clarify which action first; do not put phone in the single primary query. |
| `Je veux du sirop, c'est urgent` | request_medication, FORM and URGENCY, medication missing: clarify, no treatment selection. |
| `La pharmacie est-elle ouverte ?` | pharmacy_info_hours; target pharmacy/area missing in a context-free request: clarify. |
| `Que signifie ce mot ?` | out_of_scope if unrelated to supported pharmacy functions. |

`needs_clarification=true` requires at least one nonblank French or Arabic
question. When false, both questions are null. Questions must request missing
information, never prescribe, diagnose or suggest a substitute. Out-of-scope
advice is routed for refusal, not disguised as a clarification about how much to
take. Schema validation can check consistency, not the safety of arbitrary text;
the later pipeline must use safe templates and refusal tests.

## 5. Five examples per intent per language variety

The complete [annotated example catalogue](examples/nlu_annotation_examples.md)
contains **200 authored examples**: 8 intents × 5 varieties × 5 examples. The
[canonical JSON records](examples/nlu_annotation_examples.json) include source,
review status, language, primary intent, exact entity offsets/links, expected
clarification flag and action. A subset of short strings can legitimately occur
in more than one intended variety; the annotation context is explicit and all
labels require review.

The original specification examples are `source=authored_unreviewed`,
`review_status=pending_native_speaker_review`. They are not patient data,
pharmacy facts, a training split, the hand-verified gold set or ASR transcripts.
Advice-request examples demonstrate refusal triggers; no advice answers are
included. Brand strings are illustrative mentions with no normalized identity.

### Additional annotation examples and span conventions

These are illustrative development annotations, **not gold rows**. They make no
claim about real pharmacy identity, stock, medication facts or correct treatment.

| Message | Entity substrings / association |
| --- | --- |
| `Je cherche Doliprane 500 mg en sirop, urgent` | MEDICATION `Doliprane`; DOSAGE `500 mg` with DOSAGE_OF → medication; FORM `sirop`; URGENCY `urgent`. |
| `رقم صيدلية المثال؟` | PHARMACY_NAME `المثال`; generic `صيدلية` excluded. Example name is fictional. |
| `Téléphone de Pharmacie Exemple ?` | PHARMACY_NAME `Exemple`; generic `Pharmacie` excluded without evidence of the real registered name. |
| `بغيت لدوليبران` | MEDICATION `دوليبران`; attached `ل` excluded. |
| `واش فمراكش كاينة صيدلية؟` | LOCATION `مراكش`; attached `ف` excluded. |
| `عندكم وبانادول؟` | MEDICATION `بانادول`; attached `و` excluded. |
| `الثمن ديال ببانادول؟` | MEDICATION `بانادول`; attached `ب` excluded. |
| `Le prix d’Augmentin et de l'amoxicilline ?` | MEDICATION `Augmentin`, `amoxicilline`; exclude `d’` and `l'`. |
| `الحراسة الليلة / had lila / ce soir` | TIME_REF is the entire expression for each occurrence. |
| `Je veux 2 boîtes de Doliprane` | QUANTITY `2 boîtes`, MEDICATION `Doliprane`, QUANTITY_OF → medication. |

For check_availability, request_medication and price_inquiry, absence of an
**affirmed** named MEDICATION requires `needs_clarification=true`. Do not annotate
`ce médicament` or `هاد الدوا` as a fabricated medication name. Annotation spans
must not overlap, including FORM versus a QUANTITY mentioning tablets.

### Dataset provenance and final evaluation

Dataset model: `NLUAnnotation`; exported contract:
[nlu_annotation.schema.json](nlu_annotation.schema.json).
Creation provenance and verification belong to annotation records, not inferred
patient request facts in the public response.

Every JSONL row has `relations`, `needs_clarification`,
`contains_out_of_scope_request`, `source`, and `verified`. Creation sources are
`assistant_seed`, `synthetic`, `llm`, or `human`. Assistant/synthetic/LLM rows have
`verified=false`. Validation checks structure, not human authorship or truth.
`data/nlu/dev_seed.jsonl` is development only and must **never** become the final
evaluation set. `gold_human.jsonl` is initially empty and accepts only separately
human-authored/collected, checked rows with `source="human", verified=true`.
See [human annotation instructions](gold_annotation_howto.md).

Draft proposals may additionally carry `draft` metadata (source line, supplied
intent/notes, review warnings and exact duplicate references). These records
remain `source=assistant_seed`, `verified=false`, `split=review_only`. The
review queue may preserve flagged copies of development messages for correction;
accepted datasets remain unique. Draft proposals are never train or final
evaluation inputs. See [the import guide](gold_draft_import.md).

## 6. Public output models

Implementation: [schemas.py](../src/pharma_assistant/api/schemas.py).
Export: [response_v1.schema.json](response_v1.schema.json).
Examples: [response_v1_samples.json](examples/response_v1_samples.json).

| Field | Contract |
| --- | --- |
| request_id | Required UUID, serialized as a JSON string. Generation is the later pipeline's responsibility. |
| input | modality text/voice; original raw_text; optional transcript; language from the five supported varieties. |
| input.raw_text | Required string, at most 10,000 code points; nonblank for text input. May be empty for voice because there is no original text. |
| input.transcript | Null for text; nonblank string, at most 10,000 code points, for voice. A supplied voice raw_text does not override transcript offset basis. |
| intent | One canonical label and explicit finite numeric confidence in [0,1]. No automatic confidence default. |
| entities | List of the eight discriminated entity types with verbatim surface text. No hallucinated source spans. |
| relations | Directed QUANTITY_OF / DOSAGE_OF mention links; serialized keys type, from, to. Default empty list for response compatibility; required in JSONL. |
| contains_out_of_scope_request | Strict boolean, true for an additional unsupported clause. Default false in responses; required in JSONL. |
| pharmacy_query | needs_pharmacy_info with info_type phone/location/hours iff the primary intent is the matching pharmacy-info intent. Optional location_text is a raw affirmed LOCATION mention. For all other intents the flag is false and other fields null. |
| needs_clarification | Strict boolean, consistent with question presence. Missing affirmed medication for request/availability/price requires true. |
| clarification_question | French/Arabic question fields, at least one populated iff clarification is true. |
| disclaimer | Fixed default and only accepted value: `Cet assistant ne fournit pas de conseil médical.` |
| latency_ms | Strict nonnegative integer elapsed processing time. Schema fixtures use zero as a sentinel, not a latency result. |

Additive refinements to the original AGENTS example: optional paired raw-text
offsets, assertion status, entity_id and medication_ref. Original single-medication
shapes remain accepted. Strict entity variants prevent an accidental quantity
field on a medication. Numeric strings and booleans are not accepted as quantity,
strength, confidence, offsets or latency values. Confidence scores in fixtures
are explicitly illustrative sentinels, not calibrated estimates.

The schema enforces unique mention IDs, valid medication links, exact evidence
spans and directory-query consistency. Pydantic model validators enforce
cross-field requirements. Standard JSON Schema captures field types, enums,
ranges and tagged unions, but does **not** encode all semantic cross-field rules:
consumers needing identical validation must use AnalysisResponse.model_validate.
Neither validator performs catalogue lookup, factual verification, language
identification, diagnosis detection or actual NLU extraction.

Null versus missing: documented nullable fields have defaults and may be omitted
at validation time; normal model_dump(mode="json") includes them as null. Do not
use exclude_none/exclude_defaults for canonical response serialization. Required
container fields (intent, entities, pharmacy_query, clarification_question) must
be present even when an entity list is empty. Unknown keys are rejected.

## 7. Reproducible schema export and review

From the repository root, after make install:

```bash
uv run --frozen python scripts/export_schema.py
uv run --frozen pytest tests/test_schemas.py -v
make lint
make test
```

The export command deterministically writes docs/response_v1.schema.json from the
Pydantic model; --output selects a different path. It does not import datasets,
contact an API or download a model. Tests check artifact/model consistency,
valid examples, invalid values and cross-field edge cases, Unicode offsets,
multi-medication association, and the 8×5×5 annotation coverage matrix.

Review checklist for the user: confirm the primary-intent priority, terminology,
entity boundaries, clarification policy, intended Darija/French phrasing and
additive association fields. Native-speaker validation is still required.
This amendment is limited to annotation/schema/data validation; TASK 6 has not started.
