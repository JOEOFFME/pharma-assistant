# Medication reference and matching - TASK 4

**France BDPM fallback, not Moroccan market coverage.**

The Moroccan CNOPS open-data listing was found, but the portal/API returned
HTTP 503 on 2026-10-26. No commercial listing was scraped. Official French
bulk specialty/composition/presentation files are used instead.

Loaded specialties: **15883**.
Alias records: **161618**.
With source active-substance names: 15881.
With a product-name strength fragment: 12689.
With at least one source presentation: 14620.

No Arabic official brand names or Moroccan PPV values are supplied:
brand_name_ar and price_ppv remain null. Arabic/Arabizi/typo aliases are
programmatic and flagged synthetic; they are not approved product names.

## Source provenance

Producer: Base de données publique des médicaments (ANSM/HAS/UNCAM), France.
Source and update dates must accompany reuse. This derived prototype is
not an official service or endorsement; data may have changed since capture.
[Download terms](https://base-donnees-publique.medicaments.gouv.fr/telechargement)
[Licence Ouverte 1.0](https://base-donnees-publique.medicaments.gouv.fr/docs/telechargement/licence_bdpm.pdf)

| File | Published date observed on source page | SHA256 of original bytes |
| --- | --- | --- |
| CIS_bdpm.txt | 2026-09-29 | `332b95926f76f1a2ab3d70cdf64205397fc13e74b7cc9afad9b625fbb6961640` |
| CIS_COMPO_bdpm.txt | 2026-09-29 | `90a6e8ee286b6245c3938dd417ac75d1135a61b15ba50cfad70ee6b3bd181b7a` |
| CIS_CIP_bdpm.txt | 2026-10-26 | `276207db57839385d2d6e6ba79feb04af56ac78f288bb5bb0f2cbb1cda901164` |

## Evaluation on 50 authored review queries

This is an unreviewed, small, purposive mini-set, not a gold or independent
test distribution. Expected sets were labelled from the source catalogue.
Underspecified queries accept any listed family/attribute-compatible ID;
a correct hit does not mean unique product identification. The matcher
retains ambiguity flags. These labels require the user's review.

| Measure | Value |
| --- | ---: |
| Top-1 acceptable-ID accuracy | 50/50 (100.00%) |
| Top-3 acceptable-ID accuracy | 50/50 (100.00%) |
| Queries with multiple acceptable IDs | 37 |

Source labels: [50 queries](examples/medication_queries_50.json).
Predictions and count provenance: [results](medication_query_results.json).

## Failures

No top-1 errors on this limited, unreviewed mini-set.

## Rebuild

```bash
make medications
```

Rebuild uses committed compressed source bytes and verifies hashes; no network
is required. See [data instructions](../data/medications/README.md).

## Semantics and limitations

Brand_name is a derived lexical family; full_name preserves the source label.
DCI holds source SA active-substance names, not a newly verified WHO-INN mapping.
Laboratory holds the source marketing-authorization holder, not an inferred
manufacturer. Presentation combines source labels; no package is selected for the user.
DOSAGE is a verbatim product-strength fragment, never a recommended regimen.
Source authorization and marketing statuses are preserved, including withdrawn
or non-marketed records. They do not establish Moroccan authorization or stock.
Similarity scores combine RapidFuzz and character TF-IDF. They are not probabilities.
Explicit strengths/forms constrain candidates. Approximate spellings can still
collide; close alternatives require clarification, not automatic substitution.
Phonetic rules and generated Arabic spellings require native-speaker review.
Synthetic aliases are not canonical Arabic names and are not evaluation gold.
No diagnosis, dosage advice, therapeutic equivalence or substitution is inferred.
