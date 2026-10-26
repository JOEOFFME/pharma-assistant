# Challenge 1 - Problem study and related work

Status: TASK 1 deliverable, awaiting user validation. Sources checked on
2026-10-26. This is a focused engineering review, not a systematic literature
search. Primary papers and project-maintained documentation were consulted.
No training, dataset ingestion or ASR experiment was performed in this task.

## 1. Problem statement and scope

A patient sends a short text or voice message to a pharmacy in Modern Standard
Arabic (MSA), Moroccan Darija in Arabic script, Latin-script Darija (Arabizi),
French, or a mixture. The service must interpret the request and expose a
structured result to downstream software through an API. Interpretation is
separate from answering: recognizing an availability question does not establish
that the product is in stock.

The output needs an intent, extracted entities, source text/transcript, language
variety, clarification state, request identifier and disclaimer. Medication
mentions should retain the original span and, only when supported by a verified
catalogue, a normalized reference identifier and active ingredient. Pharmacy
information must come from a directory with provenance. Unknown values stay
unknown. A directory is not a stock feed or a live on-duty roster.

Within scope: medication request formulation, availability/price inquiry
interpretation, pharmacy phone/location/hours lookup, greetings, clarification
and explicit out-of-scope handling. Extracting a strength stated by the user is
allowed; recommending a dose, diagnosis or replacement is forbidden. The system
must not infer that two products are therapeutically interchangeable.

Illustrative messages below are author-written design examples, not collected
patient data, verified medication records or evaluation samples:

| Input variety | Example | Intended interpretation |
| --- | --- | --- |
| Darija Latin | `wach kayn Doliprane 1000 mg?` | Availability inquiry; retain stated name and strength. |
| Darija Arabic | `واش عندكم هاد الدوا؟` | Availability inquiry with unresolved medication; clarify. |
| MSA | `أين تقع الصيدلية؟` | Pharmacy location request. |
| French | `je voudrais 2 boîtes` | Medication request with stated quantity, missing medication. |
| Mixed | `bghit une boîte, machi jouj` | Request with a quantity correction/negation requiring context. |

Taxonomy, entity boundaries and final schema are finalized in TASK 2, not here.

## 2. Linguistic and operational challenges

| Challenge | Failure to prevent | Proposed response and later verification |
| --- | --- | --- |
| Code-switching within one sentence | Routing all words through an Arabic-only model drops French cues. | Preserve all scripts; compare multilingual and Arabic-focused encoders on the same mixed-language slice [R03], [R06], [R07]. |
| Darija orthographic variation | Different spellings become unrelated features or false unknowns. | Keep raw text; create a conservative normalized view and reviewed alias lexicon informed by DODa [R01], [R02]. |
| Arabizi numerals `3`, `7`, `9` | Blind replacement corrupts strengths, quantities or product identifiers. | Map only within eligible lexical tokens; preserve numeric expressions such as `500 mg` and maintain offset alignment. Validate rules with native speakers; mappings are context dependent. |
| Arabic diacritics, tatweel, alef/ya variants | Aggressive normalization merges distinct strings or breaks entity offsets. | Normalize for retrieval while extracting spans against the original text with an alignment map; ablate each transformation. |
| Brand-name transliteration and misspelling | A close string is silently resolved to the wrong product. | Retrieve multiple candidates from a verified catalogue; use exact aliases first, then character similarity; keep ambiguous matches unresolved [R11], [R12]. |
| Short/noisy voice messages | ASR loses a brand, a negation or a number; silence yields spurious content. | Validate audio, use VAD, retain transcript, ask clarification; measure medication and number preservation as well as WER/CER [R09], [R10]. |
| Very short language-ID input | `salam` or a brand is assigned a confident dialect label without evidence. | Treat language-ID as a hint; preserve user hints and mixed-script evidence; do not let it prevent extraction. |
| Negation, corrections and multiple medications | `pas X, Y` becomes a request for both; quantities attach to the wrong item. | Annotate negation/correction examples and medication-to-attribute relations; defer unresolved associations rather than flattening them. |
| Missing pharmacy information | Empty phone/hours fields become invented answers. | Return unknown with source metadata; keep directory coverage and on-duty freshness separate. |
| Domain shift and synthetic data | Template variants appear in both train and test, inflating scores. | Split by template family and preserve a human-verified held-out set; keep external general corpora separate. |

These responses are project design proposals. The cited work motivates them;
it does not certify their effectiveness for this application.

## 3. Related work

Each item identifies the evidence, its relevance and its transfer limit. Source
existence and the stated broad contribution were checked; dataset access,
checkpoint licensing and local performance still require the manual checks in
section 7. No published score is presented as our result.

### R01 - Darija Open Dataset (DODa), 2021

Outchakoucht and Es-Samaali describe a collaborative Darija-English resource
with spelling and linguistic variation [R01]. It is relevant to lexicon design
and the review of informal spellings. It is not an annotated pharmacy intent/NER
corpus and cannot supply medication facts. Its vocabulary should be reviewed
before use; a publication's licence description does not replace checking the
exact downloaded revision.

### R02 - DODa version 2, 2024

The follow-up describes expanded Darija resources including Arabic and Latin
scripts [R02]. This motivates testing both scripts instead of treating Darija
as Arabic-script-only. It remains general-language material, not clinical or
pharmacy supervision. R01 and R02 describe one evolving resource family, not
independent test sets. Snapshot selection and overlap must be checked.

### R03 - DarijaBanking, online publication 2024

Skiredj, Azhari, Berrada and Ezzini study Moroccan Arabic intent detection with
parallel banking queries across Darija, MSA, English and French [R03]. This is a
close methodological precedent for multilingual domain-specific intents and
reviewed translations. Banking labels cannot be reused as pharmacy labels;
translated queries do not establish coverage of spontaneous patient speech.

### R04 - MASSIVE, ACL 2023

FitzGerald et al. release a multilingual assistant NLU dataset supporting intent
classification and slot filling [R04]. It supplies a useful experimental model
for shared intent/entity evaluation. Its assistant domains and label inventory
are not the project specification; it does not establish Moroccan pharmacy or
Arabizi coverage. Locale availability, licence and label alignment need checking
before any auxiliary training.

### R05 - Dialectal Arabic named entity recognition, 2014

Zirikly and Diab's *Named Entity Recognition System for Dialectal Arabic* is a
verified precedent for dialectal entity extraction [R05]. Its existence helps
situate NER beyond MSA. It is not evidence of a Darija medication recognizer.
**[TO VERIFY]** Inspect the full paper and released data for dialect composition,
entity types, access and transfer suitability before selecting a dataset.

### R06 - XLM-R, ACL 2020

Conneau et al. study multilingual pretraining and cross-lingual transfer,
including NER [R06]. XLM-R is a sensible first shared encoder candidate for
Arabic/French code-mixing. This is an engineering hypothesis; multilingual
coverage does not prove good Arabizi tokenization or Darija pharmacy accuracy.
It requires intent and token-classification fine-tuning with our labels.

### R07 - CAMeLBERT, 2021

Inoue et al. compare Arabic pretraining variants, data sizes and downstream
tasks [R07]. Their findings motivate comparing variant fit, rather than choosing
only by model size. A dialectal or mixed CAMeLBERT checkpoint is an Arabic-focused
candidate. Neither a generic dialect label nor those experiments establishes
Moroccan/French mixed-input performance. Check exact checkpoint/tokenizer cards.

### R08 - AraBERT, 2020

Antoun, Baly and Hajj introduce Arabic pretrained representations [R08]. The
maintainer's preprocessing guidance is checkpoint specific [R08a]. AraBERT is an
Arabic-focused comparison candidate, with French/Arabizi coverage an open
question. Apply the selected checkpoint's expected preprocessing without losing
alignment to raw entity spans; do not assume all variants need identical
segmentation.

### R09 - Whisper, ICML 2023

Radford et al. study multilingual speech recognition through large-scale weak
supervision [R09]. This supports evaluating multilingual Whisper as the initial
ASR family. It does not provide our WER on Moroccan pharmacy recordings or
establish reliable recognition of uncommon brands and strengths. Evaluate on
user-recorded, consented audio; keep transcription separate from translation.

### R10 - faster-whisper implementation

The maintained project implements Whisper inference using CTranslate2 and
exposes a VAD filter [R10]. It fits the proposed local speech adapter. Runtime
speed and memory depend on hardware, precision, decoding and batching; no
upstream benchmark is adopted as our latency. Pin package, checkpoint revision
and execution configuration before comparison.

### R11 - RapidFuzz string similarity

RapidFuzz provides edit-based and token-based string similarity; its documented
ratio is a similarity score, not an estimated medication correctness probability
[R11]. It is a candidate generator for misspellings, followed by catalogue and
attribute checks. Partial/subset token matches can hide extra strength/form
content, so they must not alone decide product identity. Character n-gram TF-IDF
is an additional project-proposed retrieval baseline, not a claimed RapidFuzz
feature.

### R12 - RxNorm terminology normalization

The US National Library of Medicine describes RxNorm as normalized drug naming
and terminology interoperability [R12]. This motivates separating product
identity, ingredient, strength and form. RxNorm concerns US products; it is not a
Moroccan catalogue, price list or availability source. No local brand-to-ingredient
mapping is inferred from this review. Access and source-specific reuse terms
must be checked before any fallback data import.

### R13 - Healthcare conversational agents review, 2018

Laranjo et al. review healthcare conversational agents and their evaluation
[R13]. This situates the project in health-related dialogue while emphasizing
that system evaluation must be explicit. The project remains a request
interpreter/directory interface. It does not inherit clinical effectiveness or
safety from unrelated chatbots; refusal and non-fabrication behavior require our
own scenario tests.

## 4. Candidate approaches and trade-offs

The table is qualitative design analysis, not benchmark results or measured
cost/latency. All accuracy comparisons remain **[TO VERIFY]** on project data.

| Approach | Fit and strengths | Costs and failure modes | Proposed use |
| --- | --- | --- | --- |
| Rules, regex and catalogue aliases | Transparent; can run without training or hosted inference; explicit number/unit parsing. | Coverage maintenance; brittle paraphrases and negation; lexicon bias. | TASK 6 floor and deterministic guards. |
| Character n-gram TF-IDF plus linear intent classifier | Modest compute; useful spelling-noise comparison. | Requires labelled data; weak long-range relations; NER needs a separate component. | Optional lightweight comparison if budget permits. |
| XLM-R intent and token-classification heads [R06] | Shared multilingual encoder; trainable span labels. | Labelled data, memory and tuning required; Darija/Arabizi quality unknown. | First Track A candidate. |
| CAMeLBERT dialectal/mixed [R07] | Arabic variant-focused comparison. | French and Latin-script transfer may be weak; checkpoint-dependent tokenizer fit. | Second Track A candidate. |
| AraBERT [R08] | Established Arabic representation baseline. | Checkpoint-specific preprocessing; no assumed mixed-language advantage. | Third candidate if compute allows. |
| LLM strict-schema extraction | Flexible phrasing and few-shot development; provider can be swapped. | Hallucinated values, prompt injection, latency/cost and external-data exposure; schema validity is not truth. | Track B, optional and disabled without configuration. |
| Shared hybrid post-processing | Same catalogue resolution and uncertainty policy for either learned track. | Matching errors can override correct spans; more components to diagnose. | Compare with and without post-processing. |
| Whisper multilingual via faster-whisper [R09], [R10] | Local ASR adapter with configurable model size and VAD. | Brand/number errors; CPU/GPU trade-offs; no local accuracy evidence yet. | Initial voice route; compare base and small. |
| Darija-adapted Whisper | Potential domain/language adaptation. | Checkpoint identity, licence, data provenance and unseen-speaker performance unknown. | **[TO VERIFY]** Optional later comparator; none selected. |

## 5. Proposed decisions and rationale

1. **Baseline before learned models.** Implement conservative normalization,
   language hints, rules and catalogue matching as a reproducible floor. This
   supports the deadline while keeping failures visible; it is not a substitute
   for the required Track A/B comparison.
2. **Benchmark multilingual against Arabic-focused encoders.** Start with XLM-R
   and CAMeLBERT; add AraBERT if feasible. Choose using development macro-F1,
   entity F1, per-variety errors, latency and resource fit. Do not name a winner
   before measuring. No encoder is installed or trained by this document.
3. **Use a provider-neutral LLM adapter.** Validate schema, reject unknown
   catalogue identifiers, bound retries/timeouts and treat user text as data.
   Keep FakeLLM tests separate from real model evaluation. Credentials and
   consent-sensitive input handling are prerequisites for hosted experiments.
4. **Make matching evidence-driven.** Preserve raw spans; search verified aliases
   and character candidates; distinguish name similarity from probability.
   Respect stated strength/form constraints. Keep multiple candidates when
   ambiguous and ask clarification rather than suggesting substitutions.
5. **Use multilingual Whisper initially.** Transcribe in the source language;
   do not translate French/Darija to English before extracting. Compare sizes on
   the same recordings, with identical decoding controls and recorded hardware.
   A Darija-specific checkpoint remains unselected pending verification.
6. **Separate knowledge sources from language interpretation.** SQLite holds
   provenance-bearing medication and pharmacy tables. Never create stock, price,
   phone, opening hours or on-duty facts from language-model knowledge. A request
   for an unknown fact can still be interpreted successfully.
7. **Preserve uncertainty and privacy.** Missing medication, ambiguous identity,
   unsupported facts and unreliable transcription trigger clarification or an
   explicit unknown. Keep patient text/audio out of ordinary logs and public Git;
   store consented evaluation data separately. Include the required disclaimer
   in analysis responses. These are design requirements, not implemented claims.

Conceptual pipeline (detailed architecture is a later deliverable): text or
validated audio -> optional ASR -> raw text plus normalized/aligned view ->
intent/entity extraction -> catalogue candidate resolution -> uncertainty and
scope checks -> schema-validated JSON. The same final checks apply to every track.

## 6. Evaluation design and evidence boundaries

No metric values exist for this project yet. Planned evaluations are:

- Intent accuracy, macro-F1 and confusion matrix, broken down by language variety.
- Strict entity span/type precision, recall and F1 per entity type; explicitly
  document raw-text offsets, subword alignment and matching conventions.
- Medication top-1/top-3 reference resolution on reviewed queries, plus unknown
  rejection and ambiguous-name error analysis. Keep extraction and resolution
  metrics separate and report coverage of catalogue-supported cases.
- WER and CER on user-recorded reference transcripts, with normalization rules
  recorded, plus preservation of medication strings, negations and numbers.
- End-to-end JSON validity, clarification behavior and refusal of dosage,
  diagnosis or substitution advice, including mixed advice/availability inputs.
- p50/p95 end-to-end latency with hardware, warm-up, sample count, timeout/error
  count and model/config revision saved; show ASR latency separately.
- Ablations: normalization on/off, fuzzy resolution on/off, rules vs A vs B vs
  hybrid. Use identical test items and disclose any unavailable track.

Following AGENTS.md, the later dataset task requires a hand-style seed set of at
least 150 utterances and a human-verified gold set of at least 100; these are
requirements, not claims about existing data. Split by template family and keep
paraphrases/translations of the same seed in one split. Record synthetic/LLM
provenance. For audio, keep speakers/recording sources separate where feasible.
Freeze thresholds on development data, never on the gold set. Save predictions,
references, split hashes and config so every reported value can be recomputed.

## 7. Manual verification queue and missing inputs

The queue below distinguishes verified resource existence from suitability and
permission to use a particular snapshot. No dataset or checkpoint is adopted yet.

| Resource/input | What is established | Manual check before use |
| --- | --- | --- |
| DODa [R01], [R02] | Publications describe Darija spelling and script resources. | **[TO VERIFY]** Exact repository/snapshot, downloadable files, licence, Arabic/Latin alignment and native-speaker quality. |
| DarijaBanking [R03] | Published banking intent resource exists. | **[TO VERIFY]** Download route, licence, annotation process and usefulness of parallel examples; exclude banking labels from pharmacy gold. |
| MASSIVE [R04] | Published multilingual intent/slot dataset exists. | **[TO VERIFY]** Arabic/French locales, schema, current access/licence and auxiliary-label compatibility. |
| Dialectal Arabic NER [R05] | Paper and bibliography are verified. | **[TO VERIFY]** Full-text dialect/entity details, data access and permissions; no assumption of Darija medication labels. |
| XLM-R, CAMeLBERT, AraBERT [R06]-[R08] | Papers/maintainer resources exist. | **[TO VERIFY]** Exact checkpoint ID and immutable revision, weight/tokenizer licences, memory needs, preprocessing and token coverage. |
| Whisper/faster-whisper [R09], [R10] | ASR family and inference implementation exist. | **[TO VERIFY]** Weight revision, package pin, separate model/code licences and local runtime compatibility. |
| Darija-adapted Whisper | No candidate selected or verified. | **[TO VERIFY]** Existence, owner, immutable revision, licence, training provenance, overlap with evaluation and genuine Darija support. |
| Moroccan medication reference | No source file supplied in this workspace. | Ask the user for a file in TASK 4; otherwise propose a source and check access/reuse terms before any scraper. Validate product/strength/form provenance. |
| Pharmacy fetch script/directory | AGENTS.md mentions an existing Overpass script; it was not supplied here. | Obtain the script in TASK 3; check current Overpass usage policy before requests, source attribution and actual city/phone/hours coverage. |
| Price, stock and garde feeds | No verified live feed supplied. | Obtain authoritative sources and timestamps or expose unknown; do not infer from OSM alone. |
| Pharmacy NLU and voice gold sets | No reviewed dataset or user-recorded audio supplied. | Native-speaker annotation/adjudication and recording consent; meet later-task size requirements without claiming generated items are verified. |
| RxNorm [R12] | US terminology normalization resource exists. | **[TO VERIFY]** Access and source-specific reuse restrictions; never represent it as a Moroccan product list. |

Deadline implication: a tested baseline/API can be demonstrated before learned
models and voice evaluation are complete. A demonstration with missing data or
unreviewed examples must be labelled accordingly. The full challenge is complete
only when each required implementation and evaluation artifact exists; the
literature review alone cannot resolve the missing inputs.

## 8. References and verification record

Entries use author/publisher or maintainer pages. Verification date for all:
2026-10-26. For papers, verification covered identity and the contribution used
above, not a full replication. Web documentation is mutable; re-check and pin the
selected revisions when implementing. Reference identifiers resolve to the URLs
below; they are suitable for independent manual review.

- [R01] Aissam Outchakoucht and Hamza Es-Samaali (2021). *Moroccan Dialect
  -Darija- Open Dataset*. arXiv:2103.09687. Author-posted paper abstract consulted.
- [R02] Aissam Outchakoucht and Hamza Es-Samaali (2024). *The Evolution of Darija
  Open Dataset: Introducing Version 2*. arXiv:2405.13016. Author-posted abstract consulted.
- [R03] Abderrahman Skiredj, Ferdaous Azhari, Ismail Berrada and Saad Ezzini
  (published online 2024-12-05). *DarijaBanking: A new resource for overcoming
  language barriers in banking intent detection for Moroccan Arabic speakers*.
  Natural Language Processing, Cambridge University Press. Publisher abstract
  and corpus description consulted; journal issue year may differ from online year.
- [R04] Jack FitzGerald et al. (2023). *MASSIVE: A 1M-Example Multilingual Natural
  Language Understanding Dataset with 51 Typologically-Diverse Languages*.
  ACL 2023. ACL abstract consulted.
- [R05] Ayah Zirikly and Mona Diab (2014). *Named Entity Recognition System for
  Dialectal Arabic*. EMNLP Workshop on Arabic NLP, pp. 78-86.
  DOI: 10.3115/v1/W14-3610. Bibliographic page consulted; full-text transfer
  suitability intentionally marked for verification.
- [R06] Alexis Conneau et al. (2020). *Unsupervised Cross-lingual Representation
  Learning at Scale*. ACL 2020. ACL abstract consulted.
- [R07] Go Inoue, Bashar Alhafni, Nurpeiis Baimukan, Houda Bouamor and Nizar Habash
  (2021). *The Interplay of Variant, Size, and Task Type in Arabic Pre-trained
  Language Models*. arXiv:2103.06678; accepted to WANLP 2021. Author-posted abstract
  and CAMeL-Lab repository consulted.
- [R08] Wissam Antoun, Fady Baly and Hazem Hajj (2020). *AraBERT: Transformer-based
  Model for Arabic Language Understanding*. OSACT 2020. ACL publication page consulted.
- [R08a] aub-mind maintainers. *AraBERT repository*, preprocessing section.
  Implementation guidance, not an additional independent research study.
- [R09] Alec Radford et al. (2023). *Robust Speech Recognition via Large-Scale
  Weak Supervision*. ICML, PMLR 202:28492-28518. Publisher abstract consulted.
- [R10] SYSTRAN maintainers. *faster-whisper repository*. README and VAD section.
  Implementation resource, not an independent Darija benchmark.
- [R11] RapidFuzz maintainers. *rapidfuzz.fuzz documentation*. Similarity definitions
  and token-subset behavior consulted. Implementation resource.
- [R12] US National Library of Medicine. *RxNorm Overview*. Naming and geographic
  scope consulted. Official terminology documentation.
- [R13] Liliana Laranjo et al. (2018). *Conversational agents in healthcare:
  a systematic review*. JAMIA 25(9):1248-1258. DOI: 10.1093/jamia/ocy072.
  Publisher/PMC abstract and evaluation scope consulted.

[R01]: https://arxiv.org/abs/2103.09687
[R02]: https://arxiv.org/abs/2405.13016
[R03]: https://www.cambridge.org/core/journals/natural-language-processing/article/darijabanking-a-new-resource-for-overcoming-language-barriers-in-banking-intent-detection-for-moroccan-arabic-speakers/CEA99875FE7F18DBFBE9E8F4DC5B64DB
[R04]: https://aclanthology.org/2023.acl-long.235/
[R05]: https://aclanthology.org/W14-3610/
[R06]: https://aclanthology.org/2020.acl-main.747/
[R07]: https://arxiv.org/abs/2103.06678
[R08]: https://aclanthology.org/2020.osact-1.2/
[R08a]: https://github.com/aub-mind/arabert
[R09]: https://proceedings.mlr.press/v202/radford23a.html
[R10]: https://github.com/SYSTRAN/faster-whisper
[R11]: https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html
[R12]: https://www.nlm.nih.gov/research/umls/rxnorm/overview.html
[R13]: https://academic.oup.com/jamia/article/25/9/1248/5052181
