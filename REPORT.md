# ClockEffectBench reproduction

The standalone package reproduces the benchmark performance claims from the shipped
parsed predictions and published outcomes. The reproduction covers the
ClockEffectBench results, Figure 4h-j, Extended Data Figure 23, and the
exported S18 worksheet. Source checksums are retained.

## Published findings

Values below are computed from the exported records. Brackets are 95%
intervals. Full precision results are in `reference_results/reproduced_metrics.json`.

| Measure | Manuscript | Reproduced |
| --- | --- | --- |
| Published contrasts, papers, series | 580, 93, 125 | 580, 93, 125 |
| Shared paper-group results and papers | 110, 32 | 110, 32 |
| Lower calls | 10/16 | 10/16 |
| Higher calls | 30/36 | 30/36 |
| Nulls kept null | 51/58 | 51/58 |
| Balanced accuracy | 0.78 [0.68, 0.86] | 0.7792 [0.6788, 0.8641] |
| Published significant effects with matching sign | 51/52 | 51/52 |
| Significant in the published direction | 40/52 | 40/52 |
| Significant in the opposite direction | 0 | 0 |
| Paper-group direction AUROC | 1.00 [0.98, 1.00] | 0.9965 [0.9810, 1.0000] |
| Atlas direction when both significant | 25/26 | 25/26 |
| Atlas direction AUROC | 0.98 [0.91, 1.00] | 0.9793 [0.9127, 1.0000] |
| Atlas shared call agreement | 82% of 93 | 81.7204% of 93 |
| Welch-only shared call agreement | 69% of 93 | 68.8172% of 93 |
| Paired improvement in percentage points | 13 [5, 22] | 12.9032 [5.2618, 21.5692] |
| Effects in years and papers | 30, 7 | 30, 7 |
| Year-effect Spearman correlation | 0.61 [0.27, 0.93] | 0.6071 [0.2725, 0.9313] |
| Median absolute difference in years | 1.5 | 1.5137 |
| Welch-only significant recovery | 33/54 | 33/54 |
| Unrecovered significant results with 0.05 < P < 0.10 | 5 | 5 |

The atlas gain resamples 43 papers in 115 shared covered records, of which
93 have classifiable calls. Keeping that full sampling universe reproduces
the source interval. AUROC 1.00 is rounded from 0.9965277778 for the main
paper-group analysis. The additional individual-reader variant has AUROC
1.00 exactly with interval [1.00, 1.00]; the variants are kept separately.

## Language models without data

The manuscript reports model ranges of 5-6/16 decreases, 12-28/36 increases,
23-47/58 nulls, and balanced accuracy 0.46-0.52. The individual rows below
reproduce the archived Figure 4 table and bootstrap intervals.

| System | Lower | Higher | Null | Balanced accuracy with 95% CI |
| --- | --- | --- | --- | --- |
| Always higher | 0/16 | 36/36 | 0/58 | 0.3333 [0.3333, 0.3333] |
| GPT-4.1 | 6/16 | 28/36 | 23/58 | 0.5164 [0.4157, 0.6202] |
| GPT-5.5 | 6/16 | 17/36 | 38/58 | 0.5008 [0.3520, 0.6360] |
| GPT-6 Astra | 5/16 | 16/36 | 47/58 | 0.5224 [0.3862, 0.6531] |
| GPT-6 Luna | 5/16 | 12/36 | 42/58 | 0.4567 [0.3124, 0.5872] |
| GPT-6 Sol | 5/16 | 15/36 | 43/58 | 0.4902 [0.3536, 0.6231] |

## Agent reruns

The manuscript ranges are 77-90% call agreement, 90-95% direction
agreement, and direction AUROC 0.977-0.995. The six raw reruns reproduce
those ranges. Recomputed calls use the verification tests on each rerun's
selected samples and reproduce the reported 78-86% range.

| Framework and model | Raw call agreement | Raw direction agreement | Raw direction AUROC | Recomputed call agreement |
| --- | --- | --- | --- | --- |
| Codex GPT-6 Astra | 82.86% of 70 | 25/27 (92.59%) | 0.978571 | 80.00% of 70 |
| Codex GPT-6 Sol | 90.28% of 72 | 25/27 (92.59%) | 0.992063 | 85.71% of 70 |
| Codex GPT-6 Luna | 77.33% of 75 | 27/30 (90.00%) | 0.981366 | 82.19% of 73 |
| Codex GPT-5.5 | 79.27% of 82 | 32/34 (94.12%) | 0.984127 | 82.28% of 79 |
| Claude Code Claude Opus 5.5 | 82.76% of 87 | 35/37 (94.59%) | 0.995238 | 86.05% of 86 |
| Biomni GPT-6 Astra | 80.88% of 68 | 24/26 (92.31%) | 0.977444 | 77.61% of 67 |

The manuscript also reports 82% call and 87% direction agreement for the
stored ClockBase agent on this task, 85% call agreement for the verified
atlas, 63-70% call and 53-70% direction agreement for the four GPT models
without data, and 80% direction agreement for always higher.

| Agent-task baseline | Call agreement | Direction agreement |
| --- | --- | --- |
| Stored ClockBase agent | 82.43% of 74 | 26/30 (86.67%) |
| Verified atlas | 84.62% of 78 | 31/33 (93.94%) |
| GPT-6 Astra without data | 70.18% of 114 | 26/43 (60.47%) |
| GPT-6 Sol without data | 68.42% of 114 | 26/43 (60.47%) |
| GPT-6 Luna without data | 63.16% of 114 | 23/43 (53.49%) |
| GPT-5.5 without data | 66.67% of 114 | 30/43 (69.77%) |
| Always higher | 32.03% of 128 | 41/51 (80.39%) |

| Shared framework set | Manuscript agreement | Reproduced agreement |
| --- | --- | --- |
| codex (68 covered; 59 classifiable) | 83% stored agent; 81-92% reruns | 83.05% stored agent; 84.75%, 91.53%, 81.36%, 83.05% reruns |
| claude_code (82 covered; 69 classifiable) | 84% stored agent; 88% rerun | 84.06% stored agent; 88.41% reruns |
| biomni (70 covered; 60 classifiable) | 82% stored agent; 83% rerun | 81.67% stored agent; 83.33% reruns |

## Expert group comparisons

These comparisons score choice and orientation of groups against frozen
complete-group calls. They do not repeat molecular preprocessing.

| Set | Manuscript agreement | Reproduced agreement | Opposite significant calls |
| --- | --- | --- | --- |
| Mouse RNA-seq with confirmed orientation | 86/87 | 86/87 | 0 |
| Mouse RNA-seq including unconfirmed orientation | 88/89 | 88/89 | 0 |
| Human DNAm with confirmed orientation | 126/128 | 126/128 | 0 |
| Human DNAm including unconfirmed orientation | 162/168 | 162/168 | 0 |

The stored agent has one mouse and ten human opposite significant calls,
also reproduced by the regression tests. Prepared human annotations cover
18 series; the frozen scored expert reference covers 16, matching the
manuscript. GSE134429 and GSE53841 are in the prepared inventory but have
no scored expert reference row.

## Annotation reuse

ComputAgeBench is public. Its two derivative annotation files retain CC
BY-SA 4.0, with source revision and attribution in `data/expert/README.md`.
They are exceptions to the compilation's CC BY 4.0 license.

Tyshkovskiy et al. is published as a Nature article, DOI
10.1038/s41586-026-10542-3, and the rodent annotation is publicly deposited
in Zenodo record 18763485. The record states a license for clock
models and software but no annotation data license. The benchmark's factual
mouse group rules and GSM lists ship with attribution and a source-terms
notice. The original annotation workbook is not redistributed.

## Dataset and interval settings

The 580 published results comprise 515 human DNA methylation results,
64 human RNA-seq results, and one mouse RNA-seq result. Balanced-accuracy
intervals use 1,000 bootstrap replicates with seed 20261005. Other intervals
use 2,000 replicates with seed 20261009. Two of the 30 year-effect results
were recomputed after removing clock outputs above 1,000 years; four rows
in the full guarded Welch variant use this guard.

Three atlas study exports required for additional sample-output coverage
are absent. The export continued with the available source files:

- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-12/public-export/studies/dnam/GSE67748.json
- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-12/public-export/studies/dnam/GSE67749.json
- Cannot proceed - required data file not found: records deposit/data/clockbase-verifier-v3-2026-09-27/final-2026-11-12/public-export/studies/dnam/GSE72778.json

These absent study exports do not enter the scored 110-record paper-group
comparison. No missing values were replaced. The 159 available clock-output
tables total 12,848,572 bytes and match their released atlas hashes.

## Validation environment

Tests compare computed metrics with archived source fixtures, including
full-precision bootstrap endpoints, and check CLI behavior, input validation,
data integrity, and bundled wheel resources. See `VALIDATION.md` for commands.

Python 3.12.13; NumPy 1.26.4; SciPy 1.11.4; pytest 9.2.0.
