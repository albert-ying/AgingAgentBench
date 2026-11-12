# ClockEffectBench

ClockEffectBench measures whether an analysis system recovers aging-clock
effects reported in published studies of public GEO data. You can evaluate
an agent, a pipeline, or a language model using the same reference outcomes.
The reference is what each paper reports for its clock, measure, and groups.
Agreement with these results measures recovery of published findings; it does
not establish that an intervention changes lifespan or that every published
finding is correct.

The published-effects dataset contains 580 contrasts from 93 papers on 125
GEO series. A separate expert task tests group choice and orientation against
complete groups defined from sample annotation for 32 mouse RNA-seq and 16
human DNA methylation series with scored results.

## Quick start

Use Python 3.10 or later. Installation requires only NumPy, pandas, and SciPy
at runtime. All scoring runs locally without API calls.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
clockeffectbench score \
  --predictions reference_results/clockbase_paper_groups.csv \
  --cohort main110 \
  --effects reference_results/effect_pairs_years.csv
pytest -q
```

The command prints JSON and writes it to
`scores/clockbase_paper_groups_main110.json`. Use `--output FILE` to choose
another destination. It recovers 10/16 published decreases, 30/36 increases,
and 51/58 null results, with balanced accuracy 0.7792 and a 95% interval of
0.6788 to 0.8641. Direction AUROC is 0.9965, with an interval of 0.9810 to
1.0000. The paper rounds these to 0.78 and 1.00.

The optional `--effects` file is a separate set of 30 effects in years from
seven papers. It uses the paper's measure with the original overflow guard,
where four results were recomputed after removing clock outputs above 1,000
years. It is independent of the selected call cohort. It gives Spearman
correlation 0.6071, an interval of 0.2725 to 0.9313, and median absolute
difference 1.5137 years. The adjusted-test reference CSV does not contain
effect estimates, so it does not silently substitute those Welch estimates.

## Evaluate your system

For each record, compare the case group with the control group using the
specified clock and measure. Preserve `record_id` in your output. Use the
paper's significance threshold, or P < 0.05 when it states none. Submit a
CSV or JSONL file with the following fields.

| Field | Requirement |
| --- | --- |
| `record_id` | Identifier from `data/published.jsonl`. |
| `call` | `higher`, `lower`, or `not significant`. |
| `direction` | Optional `higher`, `lower`, or `none`; retain the sign even for a nonsignificant result. |
| `p_value` | Optional two-sided P value between 0 and 1 for direction AUROC. |
| `effect` | Optional signed case-minus-control estimate. |
| `effect_unit` | Use `years` for an effect to enter the year-effect correlation. |

The first line of the following example is the CSV header. The example row
is copied from the shipped ClockBase reference result.

```csv
record_id,call,direction,p_value
MED-25678027-GSE25395-Horvathv1-1,not significant,higher,0.05693342772072061
```

```sh
clockeffectbench score --predictions my_predictions.csv
clockeffectbench score --predictions my_predictions.csv --cohort main110
```

The default cohort is all 580 records, with each metric restricted to the
records for which your system supplies the required fields and the reference
has an interpretable outcome. Missing rows are abstentions. A blank call
with a supplied direction is a direction-only answer and does not count as a
null call. Coverage and denominators are printed alongside the metrics.
Unknown or duplicate identifiers, invalid calls, invalid numeric values, and
contradictory signed fields are rejected. A three-way call alone cannot
recover the direction of a nonsignificant effect or a continuous AUROC score.

For comparisons with the paper, use `main110` for the five language models,
the constant rule, and ClockBase with the paper's groups. Use
`atlas_shared93` to compare verified and Welch-only atlas calls. The
`agent_task158` cohort contains 158 published results on the task's clocks
from 47 papers and 61 series. The three `agent_shared_*` cohorts restrict
comparisons to results covered by the stored agent and each framework.
Their inventories include records without classifiable published calls;
the scorer reports the smaller call denominator explicitly.

## Language-model inputs

The no-data task supplies a GEO study description, group definitions, and
neutral descriptions of the clock and measure. The model predicts direction
and significance without consulting data or external tools. The prompt also
asks for confidence and whether it recognizes the publication.

```sh
clockeffectbench prompt MED-25678027-GSE25395-Horvathv1-1
```

This prints the frozen input used by the original baseline. The repository
contains 324 such inputs, including every record in `main110`. These are
model inputs, not model responses. `clockeffectbench/prompts.py` preserves
the original neutral clock descriptions and redaction rules. For a record
without a frozen input, supply `--study study.json` with `title`, `summary`,
`overall_design`, and `n_samples` from GEO. The builder removes sentences
with result wording and reports a failure if protected result fields leak.
Group definitions can themselves reveal a likely result; the original
builder retains that limitation with a flag. Separate evaluation inputs from
the published outcomes when assessing a new system.

## Data and reference files

The [record schema](data/README.md) documents every field in
`data/published.csv` and `data/published.jsonl`, including paper identifiers,
author, year, clock, measure, group definitions, assigned GSM lists, reported
statistics, evidence location, short quotation, and per-system eligibility.
The formats contain the same records. The CSV encodes arrays and objects as
JSON strings. Missing values remain missing.

`data/clockbase_outputs/` contains 159 per-sample output tables totaling
12,848,572 source bytes, with a hash manifest. Molecular input matrices are
not bundled. [Reference predictions](reference_results/README.md) contain
parsed calls and numerical results for every scored system, including six
agent reruns, their recomputed statistics, the agent's stored results, and
the final verified atlas. They contain no raw model responses or traces.
Source hashes, timestamps, and export settings are recorded in the two
`export_notes.json` files.

ClockBase does not compute every published clock or measure, and its sample
metadata do not resolve every group. Only 110 results support the released
paper-group tests. Eligibility failures remain in the full dataset so other
systems can address them. The source labels the 65 RNA records as 64 human
and one mouse, whereas the manuscript describes all 65 as human.

## Reference performance

The first table uses the same 110 results for every system. Entries count
correct calls within each published class; the interval resamples papers.

| System | Lower of 16 | Higher of 36 | Null of 58 | Balanced accuracy with 95% CI |
| --- | ---: | ---: | ---: | --- |
| ClockBase with the paper's groups | 10 | 30 | 51 | 0.78 [0.68, 0.86] |
| GPT-4.1 without data | 6 | 28 | 23 | 0.52 [0.42, 0.62] |
| GPT-5.5 without data | 6 | 17 | 38 | 0.50 [0.35, 0.64] |
| GPT-6 Astra without data | 5 | 16 | 47 | 0.52 [0.39, 0.65] |
| GPT-6 Luna without data | 5 | 12 | 42 | 0.46 [0.31, 0.59] |
| GPT-6 Sol without data | 5 | 15 | 43 | 0.49 [0.35, 0.62] |
| Always higher | 0 | 36 | 0 | 0.33 [0.33, 0.33] |

Verified atlas rows match 82% of 93 published calls on the shared set,
compared with 69% for Welch-only rows. Their direction agrees in 25 of 26
results significant in both, with direction AUROC 0.98 [0.91, 1.00].
The six reruns match 77% to 90% of covered calls and 90% to 95% of published
significant directions. The [reproduction report](REPORT.md) gives each
rerun, its denominator, and the comparison with the manuscript.

On `agent_task158`, each agent covers a different subset. These are the
reported calls; the recomputed variants apply the verification tests to the
same systems' selected samples. Parentheses give the metric denominator.

| System | Call agreement | Direction agreement |
| --- | ---: | ---: |
| Stored ClockBase agent | 82.43% (74) | 86.67% (30) |
| Verified atlas | 84.62% (78) | 93.94% (33) |
| Codex with GPT-6 Astra | 82.86% (70) | 92.59% (27) |
| Codex with GPT-6 Sol | 90.28% (72) | 92.59% (27) |
| Codex with GPT-6 Luna | 77.33% (75) | 90.00% (30) |
| Codex with GPT-5.5 | 79.27% (82) | 94.12% (34) |
| Claude Code with Claude Opus 5.5 | 82.76% (87) | 94.59% (37) |
| Biomni with GPT-6 Astra | 80.88% (68) | 92.31% (26) |

## Expert group evaluation

The [expert annotation notes](data/expert/README.md) explain the public
ComputAgeBench group definitions, sample fields, and selection rules.
The prepared human inventory has 18 series; 16 have scored expert reference
results, matching the manuscript. To score predictions for the frozen expert
comparisons, use the identifiers in `reference_results/expert_truth.csv`.

```sh
clockeffectbench score --expert --expert-set human-confirmed \
  --predictions reference_results/expert_candidate.csv
clockeffectbench score --expert --expert-set mouse \
  --predictions reference_results/expert_candidate.csv
```

The final reference agrees in 126/128 human results with confirmed arm
orientation, 162/168 when unconfirmed rows are included, and 88/89 mouse
results. To evaluate group choice, use the complete annotated groups and
the same clock outputs and test rules on both sides. Match the `unit_id` in
the human group file to the identifier inside each expert record ID, then
compare your selected groups' call against the frozen complete-group call.
The package scores calls; it does not infer group definitions or implement
the full original molecular preprocessing and test-selection pipeline.

Tyshkovskiy et al. is published and its rodent annotation is publicly
deposited. The benchmark's factual group rules and GSM lists are included
with provenance in `data/expert/mouse_rna_groups.jsonl`. The original workbook
is not redistributed, and the cached deposit does not state a data license
for it. Its annotation reuse terms remain an open release decision.

## Metric definitions

A significant result is called higher or lower by its case-minus-control
sign; a nonsignificant result is called not significant. Balanced accuracy
is the mean recall of the published classes present. Confusion-matrix rows
are predictions and columns are published calls. Direction agreement ignores
the prediction's significance. Direction AUROC compares the signed z score
`sign(effect) * norm.isf(P / 2)` of published increases with published
decreases, with ties worth one half. P values of zero are clipped to
`1e-300`. Results without a numeric P value do not enter AUROC.

Bootstrap clusters are whole papers, sorted by the original DOI-first paper
key. Balanced-accuracy intervals reproduce the released scorer's 1,000
replicates with seed 20261005. AUROC and year-effect intervals use 2,000
replicates with seed 20261009. The manuscript describes 2,000 replicates
generally; preserving the original scorer's separate balanced-accuracy
settings reproduces its published interval. Balanced-accuracy resampling
retains every paper in the selected cohort, including unanswered records;
AUROC resampling uses records with the required scores. Comparisons require
reporting coverage as well as accuracy.

## Citation and licenses

Cite Ying K, et al., *Autonomous AI Agents Discover Aging Interventions from
Millions of Molecular Profiles*, preprint
[10.1101/2023.02.28.530532](https://doi.org/10.1101/2023.02.28.530532).
Machine-readable citation details are in [CITATION.cff](CITATION.cff).

Code is licensed under [MIT](LICENSE). The benchmark data compilation is
licensed under [CC BY 4.0](DATA_LICENSE.md). Evidence quotations come from
the cited papers and retain their source rights. The two ComputAgeBench
derivative annotation files retain CC BY-SA 4.0 as described in the expert
notes. The mouse group file records the unstated source annotation terms.
