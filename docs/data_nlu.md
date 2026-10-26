# NLU dataset statistics - TASK 5

Assistant-authored seed and candidate examples remain unreviewed.
Generated variants are flagged synthetic; no medical facts are invented.

| Split | Rows | Template families |
| --- | ---: | ---: |
| train | 520 | 18 |
| dev | 50 | 8 |
| test | 50 | 8 |

## Counts by intents

| Split | Label | Count |
| --- | --- | ---: |
| train | check_availability | 110 |
| train | greeting_smalltalk | 15 |
| train | out_of_scope | 15 |
| train | pharmacy_info_hours | 10 |
| train | pharmacy_info_location | 15 |
| train | pharmacy_info_phone | 15 |
| train | price_inquiry | 155 |
| train | request_medication | 185 |
| dev | check_availability | 10 |
| dev | greeting_smalltalk | 5 |
| dev | out_of_scope | 5 |
| dev | pharmacy_info_hours | 5 |
| dev | pharmacy_info_location | 5 |
| dev | pharmacy_info_phone | 5 |
| dev | price_inquiry | 10 |
| dev | request_medication | 5 |
| test | check_availability | 5 |
| test | greeting_smalltalk | 5 |
| test | out_of_scope | 5 |
| test | pharmacy_info_hours | 10 |
| test | pharmacy_info_location | 5 |
| test | pharmacy_info_phone | 5 |
| test | price_inquiry | 5 |
| test | request_medication | 10 |

## Counts by languages

| Split | Label | Count |
| --- | --- | ---: |
| train | ar | 98 |
| train | darija_ar | 98 |
| train | darija_latn | 98 |
| train | fr | 98 |
| train | mixed | 128 |
| dev | ar | 10 |
| dev | darija_ar | 10 |
| dev | darija_latn | 10 |
| dev | fr | 10 |
| dev | mixed | 10 |
| test | ar | 10 |
| test | darija_ar | 10 |
| test | darija_latn | 10 |
| test | fr | 10 |
| test | mixed | 10 |

## Counts by sources

| Split | Label | Count |
| --- | --- | ---: |
| train | authored_unreviewed | 100 |
| train | synthetic | 420 |
| dev | authored_unreviewed | 50 |
| test | authored_unreviewed | 50 |

## Unicode length distribution

| Split | Min | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: |
| train | 4 | 29 | 44 | 52 |
| dev | 7 | 24 | 36 | 51 |
| test | 10 | 25 | 40 | 45 |

## Held-out candidate status

Gold candidates: 100.
Human-verified gold: 0.
No gold test file is admitted or locked until per-record human review.
Family, normalized-text and template-signature leakage checks passed.
Semantic paraphrase leakage still requires human review.

Rebuild: make dataset. See [instructions](../data/nlu/README.md).
Machine-readable counts and split hashes: [nlu_stats.json](nlu_stats.json).
