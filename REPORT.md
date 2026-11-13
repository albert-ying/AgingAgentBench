# ClockEffectBench reproduction

Source run `final-2026-11-13`. The scorer reads the shipped predictions
and compares the results with independently archived source metrics.
The paper's source table is retained in [paper_table.md](reference_results/paper_table.md).
Full precision results and source comparisons are in
`reference_results/reproduced_metrics.json`.

## Published paper groups

This comparison uses the paper's assigned groups. It is distinct from the
released atlas-row comparison in the paper's summary table.

| System | Lower | Higher | Null | Balanced accuracy with interval |
| --- | --- | --- | --- | --- |
| S0 | 0/16 | 36/36 | 0/58 | 0.3333 [0.3333, 0.3333] |
| S3 | 7/16 | 26/36 | 52/58 | 0.6854 [0.5486, 0.8173] |
| S3c | 10/16 | 30/36 | 51/58 | 0.7792 [0.6788, 0.8641] |
| S3r | 10/16 | 30/36 | 51/58 | 0.7792 [0.6788, 0.8641] |
| S4:openai:gpt-4.1 | 6/16 | 28/36 | 23/58 | 0.5164 [0.4157, 0.6202] |
| S4:openai:gpt-5.5 | 6/16 | 17/36 | 38/58 | 0.5008 [0.3520, 0.6360] |
| S4:openai:gpt-6-astra | 5/16 | 16/36 | 47/58 | 0.5224 [0.3862, 0.6531] |
| S4:openai:gpt-6-luna | 5/16 | 12/36 | 42/58 | 0.4567 [0.3124, 0.5872] |
| S4:openai:gpt-6-sol | 5/16 | 15/36 | 43/58 | 0.4902 [0.3536, 0.6231] |

| System | Significant in published direction | Direction agreement | Direction AUROC with interval |
| --- | --- | --- | --- |
| S3 | 33/54 | 52/54 | 0.9655 [0.9071, 1.0000] |
| S3c | 40/52 | 51/52 | 0.9965 [0.9810, 1.0000] |
| S3r | 40/52 | 51/52 | 1.0000 [1.0000, 1.0000] |

## Published atlas rows

All cohorts preserve the source sampling universe, including rows without
classifiable outcomes. Parentheses give the number of scored calls.

| Cohort | System | Call agreement | Direction agreement | Balanced accuracy with interval |
| --- | --- | --- | --- | --- |
| own_coverage | S1 | 79.78% (89) | 30/35 | 0.6686 [0.5264, 0.8275] |
| own_coverage | S2 | 68.09% (94) | 35/40 | 0.5778 [0.4313, 0.7329] |
| own_coverage | S2c | 81.52% (92) | 36/39 | 0.6892 [0.5417, 0.8475] |
| shared_S1_S2_S2c | S1 | 80.00% (85) | 29/34 | 0.6766 [0.5357, 0.8396] |
| shared_S1_S2_S2c | S2 | 71.08% (83) | 30/34 | 0.6067 [0.4579, 0.7645] |
| shared_S1_S2_S2c | S2c | 80.72% (83) | 32/34 | 0.6824 [0.5470, 0.8395] |
| shared_S2_S2c | S2 | 68.48% (92) | 34/39 | 0.5825 [0.4334, 0.7365] |
| shared_S2_S2c | S2c | 81.52% (92) | 36/39 | 0.6892 [0.5536, 0.8397] |
| candidate_estimand_applied | S1 | 77.08% (48) | 15/19 | 0.6108 [0.4590, 0.7964] |
| candidate_estimand_applied | S2 | 61.40% (57) | 20/24 | 0.4663 [0.3203, 0.6357] |
| candidate_estimand_applied | S2c | 82.46% (57) | 22/24 | 0.6380 [0.4952, 0.8044] |

The paired atlas gain is 13.0435 [5.3191, 21.8393] percentage points
across 114 shared covered records. Atlas direction AUROC is
0.9793 [0.9127, 1.0000].

## Paper language-model cohort

This cohort is the comparison with models given the paper description in the
summary table. It uses the earlier paper-group Welch analysis.

| System | Scored calls | Balanced accuracy with interval | Direction agreement |
| --- | --- | --- | --- |
| S0 | 115 | 0.3333 [0.3333, 0.3333] | 38/54 |
| S3 | 113 | 0.6733 [0.5267, 0.8046] | 52/54 |
| S4:openai:gpt-4.1 | 115 | 0.5160 [0.4162, 0.6164] | 38/54 |
| S4:openai:gpt-5.5 | 115 | 0.5069 [0.3664, 0.6454] | 31/54 |
| S4:openai:gpt-6-astra | 115 | 0.5177 [0.3837, 0.6513] | 30/54 |
| S4:openai:gpt-6-luna | 115 | 0.4553 [0.3265, 0.5738] | 26/54 |
| S4:openai:gpt-6-sol | 115 | 0.4959 [0.3555, 0.6223] | 33/54 |

## Same-sample comparisons

Calls and Cohen's kappa are recomputed from the exported matched contrasts.

| Stage | Contrasts | Call agreement | Kappa with interval |
| --- | --- | --- | --- |
| agent | 53 | 86.79% | 0.7622 [0.6141, 0.9150] |
| released | 53 | 81.13% | 0.6631 [0.4751, 0.8222] |
| candidate | 53 | 86.79% | 0.7637 [0.6246, 0.9152] |

## Agent reruns

Each row uses its own coverage of the frozen agent task.

| Framework | System | Scored calls | Call agreement | Direction agreement | Direction AUROC |
| --- | --- | --- | --- | --- | --- |
| codex | R:gpt-6-astra:raw | 70 | 82.86% | 25/27 | 0.978571 |
| codex | R:gpt-6-astra:recomputed | 70 | 80.00% | 25/27 | 0.971429 |
| codex | R:gpt-6-sol:raw | 72 | 90.28% | 25/27 | 0.992063 |
| codex | R:gpt-6-sol:recomputed | 70 | 85.71% | 25/27 | 0.992063 |
| codex | R:gpt-6-luna:raw | 75 | 77.33% | 27/30 | 0.981366 |
| codex | R:gpt-6-luna:recomputed | 73 | 82.19% | 29/31 | 0.981366 |
| codex | R:gpt-5.5:raw | 82 | 79.27% | 32/34 | 0.984127 |
| codex | R:gpt-5.5:recomputed | 79 | 82.28% | 32/34 | 0.983516 |
| claude_code | R:claude-opus-5-5:raw | 87 | 82.76% | 35/37 | 0.995238 |
| claude_code | R:claude-opus-5-5:recomputed | 86 | 86.05% | 35/37 | 0.995074 |
| biomni | R:gpt-6-astra:raw | 68 | 80.88% | 24/26 | 0.977444 |
| biomni | R:gpt-6-astra:recomputed | 67 | 77.61% | 24/26 | 0.968254 |

## Expert group comparisons

These scores compare parsed calls with the frozen complete-group reference.

| Set | Stage | Orientation | Agreement | Opposite significant calls |
| --- | --- | --- | --- | --- |
| A1 | agent | all rows of the agent | 93/98 | 1 |
| A1 | released | all released rows | 88/89 | 0 |
| A1 | released | labels confirmed | 86/87 | 0 |
| A1 | candidate | all released rows | 88/89 | 0 |
| A1 | candidate | labels confirmed | 86/87 | 0 |
| A2 | agent | all rows of the agent | 147/192 | 10 |
| A2 | released | all released rows | 144/180 | 0 |
| A2 | released | labels confirmed | 114/130 | 0 |
| A2 | candidate | all released rows | 157/163 | 0 |
| A2 | candidate | labels confirmed | 121/123 | 0 |

## Effects in years

The effect comparison contains 30 estimates from 7 papers.
Spearman correlation is 0.6071 [0.2725, 0.9313].
Median absolute difference is 1.5137 years.

## Released atlas counts

These counts are read from the source atlas and design-check rows.

| Count | Value |
| --- | --- |
| released_rows | 63059 |
| released_human DNAm | 12289 |
| labels_unconfirmed | 2226 |
| labels_unconfirmed_human DNAm | 1010 |
| released_human RNA-seq | 24005 |
| labels_unconfirmed_human RNA-seq | 690 |
| released_mouse RNA-seq | 26765 |
| labels_unconfirmed_mouse RNA-seq | 526 |
| design checks rows | 64482 |
| design checks significant | 19103 |
| design checks applies | 7468 |
| design checks no call | 1423 |
| design checks gained | 491 |
| design checks significant lost | 436 |

## Design-error source results

The summary table's design-error counts and intervals are retained from the
source classification analysis. This package does not repeat those classifications
or refit their design-effect-adjusted intervals.

| Set | Stage | Errors | Source interval |
| --- | --- | --- | --- |
| A1 | agent | 20/98 | [0.061486, 0.435901] |
| A1 | released | 5/89 | [0.003157, 0.233466] |
| A1 | candidate | 5/89 | [0.003157, 0.233466] |
| A1 | readers | 3/89 | [0.000048, 0.263356] |
| A2 | agent | 39/44 | [0.578465, 0.993195] |
| A2 | released | 32/41 | [0.416954, 0.969593] |
| A2 | candidate | 11/41 | [0.055759, 0.612098] |
| A2 | readers | 6/41 | [0.016035, 0.451073] |

## Source coverage

The published dataset has 580 contrasts from 93
papers on 125 series. The 159 available
clock-output tables total 12,848,572 bytes and match their atlas hashes.

The following optional study exports are unavailable:

- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-13/public-export/studies/dnam/GSE67748.json
- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-13/public-export/studies/dnam/GSE67749.json
- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-13/public-export/studies/dnam/GSE72778.json

These study exports do not enter the paper-group scores. Molecular preprocessing,
source article extraction, design-error adjudication, and refitting molecular
tests are outside this reproduction. No missing measurements were substituted.

## Validation environment

Python 3.12.13; NumPy 1.26.4; SciPy 1.11.4; pytest 9.2.0.
All 528 source metric comparisons passed. See `VALIDATION.md` for commands.
