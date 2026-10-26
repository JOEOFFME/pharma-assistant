# CODEX MASTER PROMPT — Challenge #1: Arabic/Darija Patient–Pharmacy Assistance

> Paste this whole file as the first message (or save it as `AGENTS.md` at the repo root).
> Then send tasks ONE AT A TIME: "Do TASK 0", wait for my validation, then "Do TASK 1", etc.

---

## 0. ROLE & WORKING RULES

You are a senior ML/backend engineer. You are building, with me, a production-style
prototype of a **multilingual (Modern Standard Arabic, Moroccan Darija in Arabic script and
Latin script "Arabizi", and French, including code-mixed) pharmacy assistance service**.

Strict rules:
1. **Work on ONE task at a time.** Never start the next task until I write `VALIDATED TASK N`.
2. At the end of every task, output a **Validation Report**: what you built, files created/changed,
   exact commands to run, expected output, test results, known limitations, and the checklist of
   acceptance criteria with ✅/❌.
3. **Do not invent data.** If a dataset, model or file is missing, say so and propose options. Never
   fabricate medication facts, pharmacy phone numbers or evaluation numbers.
4. **Everything reproducible:** pinned dependencies, fixed random seeds, config in YAML/.env,
   no hard-coded absolute paths, no secrets in code.
5. **Tests first-class:** every task ships with `pytest` tests that I can run.
6. **Small, readable commits:** one logical commit per task (`feat(taskN): ...`).
7. If a requirement is ambiguous, ask me **at most 3 concise questions**, state your default
   assumption, and proceed with it if I don't answer.
8. Safety: the assistant must NEVER give dosage advice, diagnosis, or substitution advice. It only
   structures requests and returns pharmacy information. Add a disclaimer field in API responses.
9. Code quality: Python 3.11, type hints, docstrings, `ruff` + `black`, Pydantic v2 models,
   logging (no bare prints) in library code.

---

## 1. PROJECT GOAL (from the official statement)

Design and implement an intelligent service that helps users formulate **medication-related
requests to their pharmacies**. It must:

- Accept **text and/or voice** input.
- Support **Arabic, Darija, French** and code-mixing (e.g. "wach kayn Doliprane 1000 mg?",
  "عندكم دوليبران؟", "j'ai besoin de 2 boîtes d'amoxicilline").
- Identify the **intent** and extract **entities** (medication names, quantities, dosage/strength,
  form, pharmacy/location info requests, urgency, etc.).
- Return a **structured JSON interpretation** (not only free text).
- Be exposed through an **API**.
- Deliverables: problem study & related work, architecture/pipeline design, NLP + speech
  implementation, API service, test scenarios & evaluation of results.

### Intents (initial taxonomy — can be refined in TASK 2)
| Intent | Example |
|---|---|
| `check_availability` | "wach kayn Augmentin 1g?" |
| `request_medication` / `order_medication` | "bghit 3 dyal les boîtes dyal Doliprane" |
| `pharmacy_info_phone` | "شنو نمرة الصيدلية؟" |
| `pharmacy_info_location` | "فين كاينة أقرب صيدلية؟" |
| `pharmacy_info_hours` | "ghadi tkoun mkhellsa lyoum?" / "pharmacie de garde ?" |
| `price_inquiry` | "bch7al Panadol?" |
| `greeting_smalltalk` | "salam" |
| `out_of_scope` | anything else (incl. medical advice requests → polite refusal) |

### Entities
`MEDICATION` (raw span + normalized name + DCI/active ingredient when known), `DOSAGE`
(e.g. 500 mg), `FORM` (comprimé/sirop/injectable/…), `QUANTITY` (number + unit: boîtes, plaquettes,
flacons), `PHARMACY_NAME`, `LOCATION` (city/neighborhood), `TIME_REF` (today, tonight, now),
`URGENCY`.

### Target output schema (v1)
```json
{
  "request_id": "uuid",
  "input": {"modality": "text|voice", "raw_text": "...", "transcript": "...", "language": "darija_ar|darija_latn|ar|fr|mixed"},
  "intent": {"label": "check_availability", "confidence": 0.93},
  "entities": [
    {"type": "MEDICATION", "text": "دوليبران", "normalized": "Doliprane", "dci": "paracétamol", "confidence": 0.9, "matched_id": "med_00123"},
    {"type": "DOSAGE", "text": "1000 mg", "value": 1000, "unit": "mg"},
    {"type": "QUANTITY", "text": "2 boîtes", "value": 2, "unit": "box"}
  ],
  "pharmacy_query": {"needs_pharmacy_info": false, "info_type": null, "location_text": null},
  "needs_clarification": false,
  "clarification_question": {"fr": null, "ar": null},
  "disclaimer": "Cet assistant ne fournit pas de conseil médical.",
  "latency_ms": 123
}
```

---

## 2. RECOMMENDED STACK (propose alternatives only with justification)

- **Language/Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic v2.
- **Speech (ASR):** OpenAI Whisper family via `faster-whisper` (multilingual, handles Arabic and
  French); evaluate whether a Darija-fine-tuned Whisper checkpoint from Hugging Face improves WER
  (verify the checkpoint exists and its license before using it).
- **NLP:** two-track approach, compared in evaluation:
  - **Track A (classical/supervised):** language-ID + normalization + fine-tuned multilingual
    encoder (e.g. AraBERT / CAMeLBERT / multilingual-e5 / XLM-R — choose after a quick benchmark) for
    intent classification + token classification (NER).
  - **Track B (LLM-based extraction):** prompt an LLM with a strict JSON schema (function-calling /
    structured output), behind a provider-agnostic interface so it can be swapped or disabled.
  - **Hybrid:** rule/fuzzy matching against the medication DB as a post-processing step for both tracks.
- **Medication matching:** `rapidfuzz` + character n-gram TF-IDF + transliteration (Arabic ⇄ Latin) to
  map misspelled / transliterated brand names ("دوليبران", "doliprane", "dolipran") to the reference DB.
- **Data:** SQLite (or Postgres via SQLAlchemy) for medication + pharmacy tables.
- **Tooling:** `pytest`, `ruff`, `black`, `pre-commit`, Docker + docker-compose, `make`.

---

## 3. REPOSITORY LAYOUT (create in TASK 0)

```
pharma-assistant/
├── AGENTS.md
├── README.md
├── pyproject.toml            # or requirements.txt + requirements-dev.txt (pinned)
├── Makefile
├── .env.example
├── configs/                  # yaml configs (models, thresholds, paths)
├── data/
│   ├── raw/                  # never edited by hand
│   ├── processed/
│   ├── medications/          # reference medication DB
│   ├── pharmacies/           # pharmacy directory (from OSM + manual)
│   ├── nlu/                  # annotated utterances (train/dev/test)
│   └── audio/                # voice test set
├── src/pharma_assistant/
│   ├── api/                  # FastAPI app, routers, schemas
│   ├── asr/                  # speech-to-text
│   ├── nlp/                  # normalization, langid, intent, ner, extraction
│   ├── matching/             # medication & pharmacy matching
│   ├── pipeline/             # orchestration text/voice -> structured output
│   ├── data_tools/           # fetch/clean/build scripts
│   └── eval/                 # metrics & evaluation runners
├── tests/
├── notebooks/                # optional exploration only
├── docs/                     # study, architecture, evaluation report
└── docker/
```

---

## 4. TASKS (execute strictly in order, wait for my validation after each)

### TASK 0 — Scaffolding & tooling
**Do:** create the repo layout, dependency management, Makefile targets (`install`, `lint`, `test`,
`run`), pre-commit, `.env.example`, a health-check FastAPI app (`GET /health`), a first passing test.
**Acceptance criteria:**
- `make install && make test && make run` work from a clean clone.
- `GET /health` returns `{"status":"ok"}`.
- `README.md` has setup instructions.
**Validation Report must include:** tree output, commands run, test output.

### TASK 1 — Problem study & related-work document
**Do:** write `docs/01_problem_study.md`: problem statement, challenges (code-switching, Darija
orthographic variation, Arabizi numerals like 3/7/9, brand-name transliteration, short/noisy voice
input), related work (Darija NLP resources & corpora, Arabic/Darija intent & NER work, Whisper/ASR
for dialectal Arabic, medication-name matching/fuzzy matching, health chatbots), comparison table of
candidate approaches with justification of choices.
**Rules:** cite only sources you are confident exist; mark anything uncertain as `[TO VERIFY]` — I will
verify. No fabricated references or numbers.
**Acceptance criteria:** ≥ 8 related-work items, comparison table, justified decisions, list of
datasets/models I should check manually.

### TASK 2 — Specification: intents, entities, schema, annotation guidelines
**Do:** finalize the intent taxonomy and entity set; produce `docs/02_nlu_spec.md` and the Pydantic
models in `src/pharma_assistant/api/schemas.py` implementing the output schema above (with JSON
Schema export); write annotation guidelines with ≥ 5 examples per intent in each language variety
(Darija-Arabic script, Darija-Latin, MSA, French, code-mixed) and edge cases (multiple meds in one
message, negation, missing quantity, ambiguous dosage).
**Acceptance criteria:** schema validates sample payloads; unit tests for schema; spec reviewed by me.

### TASK 3 — Pharmacy directory (data layer #1)
**Context:** I already have a script `fetch_pharmacies.py` that queries OpenStreetMap via Overpass
and writes `pharmacies_morocco_raw.json` + `pharmacies_morocco.csv`. OSM coverage in Morocco is
patchy and `opening_hours` / on-duty ("de garde") info is mostly missing.
**Do:**
1. Move/refactor that script into `src/pharma_assistant/data_tools/fetch_pharmacies.py` (keep behavior,
   add CLI args, logging, retry/backoff, optional per-city bounding boxes if the national query times out).
2. Build `clean_pharmacies.py`: dedupe, normalize names (Arabic/French), normalize phone numbers to
   E.164 (+212…), fix city names, drop rows without coordinates, add a `data_quality` score.
3. Load into a `pharmacies` table (SQLite) with a repository class: `search_by_name`,
   `nearest(lat, lon, k)`, `by_city`.
4. Produce a coverage report (counts by city, % with phone / hours / name) in `docs/data_pharmacies.md`.
**Rules:** respect Overpass usage policy (no hammering); do NOT fabricate missing phones/hours;
document the on-duty-pharmacy gap and design the schema so garde data can be added later
(`is_on_duty`, `duty_from`, `duty_to`).
**Acceptance criteria:** table populated; `nearest()` tested with 3 known coordinates (Rabat,
Casablanca, Marrakech); coverage report generated.

### TASK 4 — Medication reference database (data layer #2)
**Do:** (a) Ask me which source file I have; if none, propose and implement an ingestion script for
a public Moroccan medication listing (e.g. the Ministry of Health / official price lists — I will
verify availability and legal terms) or a fallback open dataset, **before** writing any scraper.
(b) Build a normalized schema: `id, brand_name, brand_name_ar (if available), dci (active ingredient),
dosage, form, presentation, laboratory, price_ppv (if available), source`.
(c) Generate **aliases/variants** per medication: lowercase, no accents, Arabic transliteration,
Arabizi variants, common misspellings (generated programmatically; flag as `synthetic`).
(d) Build a `MedicationIndex` (rapidfuzz + char n-gram TF-IDF) with `search(query, k)` returning
candidates + scores.
**Acceptance criteria:** ≥ N medications loaded (report N); search tests: exact, misspelled
("dolipran"), Arabic ("دوليبران"), Arabizi ("doliprane 1000"), dosage-disambiguation; top-1 / top-3
accuracy on a 50-query handwritten mini test set that I can review.

### TASK 5 — NLU dataset creation (train/dev/test)
**Do:** build `data/nlu/` with annotated utterances (intent + entity spans) in JSONL:
- Seed set: ≥ 150 **hand-style** utterances covering all intents/languages (I will review/correct).
- Programmatic augmentation: templates × medication list × quantities × phrasing variants ×
  code-switching × Arabizi noise (3/7/9, missing vowels, typos), clearly flagged `source: synthetic`.
- Optional LLM-assisted paraphrasing behind an interface (flagged `source: llm`), with manual review of
  a sample.
- Split train/dev/test by **template family** (avoid leakage); keep a small **gold test set (≥ 100)**
  that is hand-verified and never used for training or tuning.
- Script `scripts/dataset_stats.py` (class balance, language mix, length distribution).
**Acceptance criteria:** stats report; leakage check passes; gold set locked and documented.

### TASK 6 — Text processing pipeline (baseline, no ML)
**Do:** `nlp/normalize.py` (Unicode normalization, Arabic diacritics/tatweel, alef/ya variants,
Arabizi digits mapping, punctuation, repeated letters), `nlp/langid.py` (script + lexicon heuristics →
`darija_ar|darija_latn|ar|fr|mixed`), rule-based intent & entity baseline (regex + keyword lexicons +
MedicationIndex), and `pipeline/text_pipeline.py` returning the full v1 schema.
**Acceptance criteria:** unit tests for each normalizer; baseline evaluated on gold set (intent
accuracy/macro-F1, entity-level F1) — report numbers honestly, even if low. This is our **floor**.

### TASK 7 — Learned NLU models
**Do:** implement and compare, with the same evaluation script:
1. **Track A:** fine-tune an encoder for intent classification + NER (benchmark 2–3 candidate backbones
   on dev set; keep configs in YAML; seeds fixed; log metrics to JSON/CSV).
2. **Track B:** LLM structured extraction with strict JSON schema, retries on invalid JSON, timeout,
   provider interface + a `FakeLLM` for tests.
3. **Hybrid:** model output → medication matching/normalization → confidence-based fallback and
   `needs_clarification` logic (e.g. missing medication, ambiguous dosage).
**Acceptance criteria:** results table (baseline vs A vs B vs hybrid) on dev and gold test: intent
accuracy, macro-F1, entity F1 per type, medication top-1/top-3 resolution accuracy, latency;
confusion matrix; error analysis of ≥ 20 failures by category. Model artifacts saved under `models/`
(git-ignored) with a `model_card.md`.

### TASK 8 — Speech pipeline (voice input)
**Do:** `asr/transcriber.py` using `faster-whisper` with configurable model size, language auto-detect
+ hint, VAD, audio validation (format, duration limit, sample-rate conversion via ffmpeg); build a
**small voice test set** protocol (`data/audio/README.md`: script for me to record ≥ 40 short
utterances: Darija, MSA, French, code-mixed, with noise variants) with transcripts file; evaluation
script computing **WER/CER** per language variety; optionally compare 2 ASR models (e.g. base vs
small, or a Darija-fine-tuned checkpoint if license-OK).
**Rules:** don't claim WER numbers unless computed on audio I recorded; add an ASR-error-robustness
step (post-ASR normalization, medication fuzzy re-matching).
**Acceptance criteria:** `transcribe(path)` works on a sample; WER/CER table; end-to-end
voice → structured JSON demo script.

### TASK 9 — API service
**Do:** FastAPI endpoints:
- `GET /health`, `GET /version`
- `POST /v1/analyze/text` `{text, language_hint?, user_location?}` → v1 schema
- `POST /v1/analyze/voice` (multipart audio) → v1 schema (+ transcript)
- `GET /v1/medications/search?q=` and `GET /v1/pharmacies/nearby?lat&lon&k=`
- (optional) `POST /v1/chat` — session-based dialog that asks clarification questions and answers
  pharmacy-info intents using the pharmacy DB (templated responses in the user's language variety).
Add: Pydantic validation, error model, request IDs, structured logging, CORS config, file-size limits,
rate-limit (simple), OpenAPI docs with examples, API key via env (optional), Dockerfile +
docker-compose, `make demo`.
**Acceptance criteria:** `pytest` API tests (TestClient) for success, validation errors, empty/very
long input, unsupported audio; `curl` examples in README; container builds and serves.

### TASK 10 — Test scenarios & evaluation report
**Do:** `docs/10_test_scenarios.md` with ≥ 25 end-to-end scenarios (per language, per intent, edge
cases: multi-medication, typos, noisy voice, out-of-scope, medical-advice request refusal);
automated runner producing `reports/eval_YYYYMMDD.json` and a Markdown report: metrics tables,
confusion matrix, error analysis, latency percentiles (p50/p95), ablations (normalization on/off,
fuzzy matching on/off, track A/B/hybrid), limitations & ethical considerations (privacy of health
data, no medical advice, bias toward MSA/French), future work.
**Acceptance criteria:** one command regenerates the report; every number in the report is traceable
to a saved results file.

### TASK 11 — Packaging, documentation & demo
**Do:** final README (architecture diagram in Mermaid, pipeline flow, how to run, how to
evaluate), `docs/architecture.md`, a minimal demo UI (Streamlit or static HTML) with text box + mic
upload that shows the JSON and highlighted entities, CI workflow (lint + tests), final checklist
mapping each **Expected Output** of the challenge statement to a file/section in the repo.

---

## 5. DEFINITION OF DONE (global)
- All "Expected Output" items of the challenge are mapped to repo artifacts.
- Fresh clone → `make install && make test && make demo` works.
- Evaluation numbers are reproducible and honestly reported (including failures).
- No fabricated data, citations, or metrics anywhere.

---

## 6. FIRST ACTION
Acknowledge these rules in **5 lines max**, list the 3 questions you need answered before TASK 0
(if any), then wait for me to say: **"Do TASK 0"**.
