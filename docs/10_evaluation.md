# Evaluation report — actual runs and their limits

The rule baseline uses the 84 user-reviewed draft intent labels. Entity scores
are agreement with automatically proposed spans; independent human-gold entity
accuracy has not been established. Two greetings duplicate development data.
The developer has seen these draft examples; this is exploratory evaluation.

## Reviewed draft (84 messages)

| Track | Intent accuracy | Intent macro-F1 | Provisional entity exact F1 |
| --- | ---: | ---: | ---: |
| Rule baseline | 0.8810 | 0.8770 | 0.8538 |

Source: [baseline_results.json](baseline_results.json), including every prediction,
intent confusion matrix, per-type span counts and reference SHA-256. Exact spans
match type/start/end in Unicode code points; micro F1 counts TP/FP/FN. Intent
macro-F1 averages all eight predefined classes, including zero-support classes.

## Development comparison (50 messages; not final gold)

| Track | Intent accuracy | Macro-F1 | Entity exact F1 |
| --- | ---: | ---: | ---: |
| Baseline | 0.7400 | 0.7508 | 0.9756 |
| Word TF-IDF + learned BIO | 0.2400 | 0.1938 | 0.9474 |
| Character TF-IDF + learned BIO | 0.4000 | 0.2847 | 0.9474 |
| Hybrid (conservative rule entities) | 0.7400 | 0.7508 | 0.9756 |

Sources: [supervised_results.json](supervised_results.json),
[track_comparison.json](track_comparison.json). Models were trained on 520
train rows only, with seed 42. Template families stay together. NER is a trained
BIO token classifier using local lexical/context features. The word/character
TF-IDF variants are actual lightweight alternatives, not pretrained encoder results.
The small, heavily augmented training set favors medication requests and price
questions; the low intent scores are retained. The default remains the rule
baseline. Hybrid keeps baseline entities/refusal checks and uses learned intent
only above its threshold and if schema validation succeeds.

The real LLM provider was not run: no endpoint/key is configured. FakeLLM
validates interfaces/failure behavior only. Local-encoder fine-tuning code and
pinned optional dependencies are supplied but no encoder weights or benchmark
are claimed. Consequently the requested comparison of two pretrained encoders
is still unvalidated. No encoder/LLM score is fabricated.

## Ablations and measured latency

These use the same reviewed draft; entity scores remain provisional.
Normalization-off disables entity/intent surface normalization, while catalogue
retrieval retains its built-in normalization. Resolution-off disables identity
grounding but keeps mention extraction; unchanged entity F1 is expected.

| Mode | Intent accuracy | Provisional entity F1 | Resolved mentions | P50 ms | P95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 0.8810 | 0.8538 | 10 | 1.51 | 158.93 |
| normalization_off | 0.8333 | 0.8066 | 9 | 1.65 | 164.67 |
| resolution_off | 0.8810 | 0.8538 | 0 | 0.95 | 1.28 |

Source: [ablation_results.json](ablation_results.json), including each latency
sample and prediction. These are one local CPU run, warmed pipeline, floor
quantiles; initialization, ASR and network latency are excluded. No confidence
interval/general hardware performance claim is implied.

## Twenty observed failure examples

The following are actual character-model dev intent errors. The potential
cause is a hypothesis: limited lexical/template generalization and imbalanced
synthetic training. Individual clinical facts cannot be inferred from errors.

| ID | Text | Expected | Predicted |
| --- | --- | --- | --- |
| check_availability.ar.04 | هل يتوفر دوليبران 500 mg؟ | check_availability | price_inquiry |
| check_availability.darija_ar.04 | باقي عندكم دوليبران 500 mg؟ | check_availability | price_inquiry |
| check_availability.fr.01 | Avez-vous Doliprane ? | check_availability | price_inquiry |
| check_availability.fr.04 | Avez-vous Doliprane 500 mg ? | check_availability | price_inquiry |
| greeting_smalltalk.ar.01 | السلام عليكم ورحمة الله | greeting_smalltalk | check_availability |
| greeting_smalltalk.darija_ar.01 | السلام عليكم | greeting_smalltalk | check_availability |
| greeting_smalltalk.darija_latn.01 | salam 3likom | greeting_smalltalk | check_availability |
| greeting_smalltalk.fr.01 | Bonjour | greeting_smalltalk | check_availability |
| greeting_smalltalk.mixed.01 | salam, bonjour | greeting_smalltalk | check_availability |
| out_of_scope.ar.02 | كم حبة من دوليبران يجب أن أتناول؟ | out_of_scope | request_medication |
| out_of_scope.darija_ar.02 | شحال من حبة ناخد ديال دوليبران؟ | out_of_scope | price_inquiry |
| out_of_scope.darija_latn.02 | ch7al men 7ebba nakhod dyal Doliprane? | out_of_scope | price_inquiry |
| out_of_scope.fr.02 | Combien de comprimés de Doliprane dois-je prendre ? | out_of_scope | price_inquiry |
| out_of_scope.mixed.02 | شحال de comprimés de Doliprane ناخد؟ | out_of_scope | price_inquiry |
| pharmacy_info_hours.ar.02 | متى تغلق الصيدلية؟ | pharmacy_info_hours | pharmacy_info_location |
| pharmacy_info_hours.darija_ar.02 | فوقاش كتسد الصيدلية؟ | pharmacy_info_hours | pharmacy_info_location |
| pharmacy_info_hours.darija_latn.02 | fo9ach katsed pharmacie? | pharmacy_info_hours | pharmacy_info_location |
| pharmacy_info_hours.fr.02 | À quelle heure ferme la pharmacie ? | pharmacy_info_hours | pharmacy_info_location |
| pharmacy_info_hours.mixed.02 | فوقاش ferme la pharmacie ? | pharmacy_info_hours | pharmacy_info_location |
| pharmacy_info_location.ar.03 | أين أقرب صيدلية في الرباط؟ | pharmacy_info_location | pharmacy_info_phone |

Additional error categories: unknown/transliterated medication names, missed
neighborhoods, bare package counts, generic pharmacy-name boundaries, ambiguous
strengths and short-language identification. See per-type exact TP/FP/FN in the
saved baseline results instead of treating raw agreement as medication truth.

## End-to-end and speech evidence

The scenario runner executed 40 text cases across all eight intents and five varieties: 33 primary-intent matches and 7 failures.
[Scenario table](10_test_scenarios.md) and [full results](scenario_results.json).
These development scenarios overlap authored specification examples.

Actual ASR inference and real HTTP text/search/directory/voice paths were run.
[ASR smoke](asr_smoke.json) retains the poor transcript from synthetic flite
French text spoken by an English synthesis voice. It establishes execution,
not French/Darija quality. [HTTP smoke](http_smoke.json) records actual endpoint
responses. No WER/CER is claimed on synthetic speech. Human recordings are
absent; [the recording protocol](../data/audio/README.md) supplies 40 prompts
and an evaluation manifest format.

## Reproduce

```bash
make medications
make pharmacies
make dataset
make baseline-eval
make train-nlu
uv run --frozen python scripts/compare_tracks.py
make scenarios
uv run --frozen python scripts/run_ablations.py
make lint
make test
```

Limitations: no independent >=100-row human gold; no real provider comparison;
no executed pretrained-encoder benchmark; no user-recorded WER/CER; no clinical,
live-stock or Moroccan-price validation. This prototype must not be used to
select medications or give dosage, diagnosis or substitution advice.
