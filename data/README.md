# Published clock effects

`published.jsonl` and `published.csv` contain the same 580 published contrasts
from 93 papers for 125 GEO series. One row is one paper, clock, measure, and
group comparison. The source labels 515 records as human DNA methylation,
64 as human RNA-seq, and one as mouse RNA-seq.

The paper's results are the reference outcomes. ClockBase's sample assignments
and predictions are evaluated against those outcomes. Assigned samples can
differ from a paper's reported group sizes because a deposit contains a
different subset or the available metadata do not identify every participant.
An empty assigned sample list means that no agreed assignment was retained.

`tasks.jsonl` contains the same 580 identifiers with only series, modality,
clock, measure, group labels and definitions, assigned GSM lists, and threshold.
It excludes published outcomes, effects, P values, and source quotations.
Provide this file to an evaluated system and keep the outcome files separate.

## Record fields

The JSONL format preserves structured values. In the CSV, objects and arrays
are JSON strings; empty scalar cells are missing values. `id` and `record_id`
are identical stable identifiers. Numeric values are copied from the source
records without imputation.

| Field | Meaning |
| --- | --- |
| `record_id`, `id` | Stable published contrast identifier. |
| `paper_id` | DOI, or PMID, PMCID, citation, or URL when DOI is absent; the original scorer's paper clustering key. |
| `tier` | `T1`, a published result with a reported statistic or call. |
| `gse` | GEO series accession. |
| `modality`, `tissue` | Source annotation of assay and tissue. |
| `clock_reported` | Clock and output as named by the paper. |
| `clock_clockbase` | Corresponding ClockBase output column, or null when unavailable. |
| `measure` | `age`, `acceleration_residual`, `acceleration_difference`, `rate`, or `other`. |
| `case_label`, `control_label` | Short arm labels. |
| `case_definition`, `control_definition` | The groups defined in the paper. |
| `case_gsms`, `control_gsms` | GSM lists selected identically by the two sample-assignment models, where available. |
| `groups_status` | Assignment outcome, including `AGREED` or a reason no assignment was kept. |
| `n_case`, `n_control` | Group sizes stated in the paper; null when unstated. |
| `direction` | Published case-minus-control direction: `higher`, `lower`, or `none`. |
| `significant` | Published significance as a Boolean, or null if unstated. |
| `published_call` | `higher`, `lower`, `not significant`, or null when unresolved. |
| `threshold`, `p_value`, `test` | Published significance criterion, P value, and statistical test where stated. |
| `covariates` | Adjustment variables stated in the source extraction. |
| `effect` | Published `{value, unit, type}` object, or null when unavailable. |
| `source` | Paper identifiers, first author, year, title/citation, evidence location, short quote, and source URL. |
| `eligibility` | Per-system `testable` Boolean and recorded status. |

`eligibility.S1`, `eligibility.S2`, and `eligibility.S3` describe the original
stored agent, verified row, and Welch-only paper-group analyses.
`eligibility.S4:*` describes parsed predictions of language models without
data. `eligibility.clockbase_paper_groups` describes the released analysis
using the paper's groups with the verification test rules. Coverage and
metric eligibility differ: a system may provide an answer for a record whose
published direction or significance is unstated. The scorer determines metric
eligibility from the available truth and prediction fields.

The evidence quote is a contiguous prefix of at most 25 whitespace-delimited
words from the first extracted source passage. It is an evidence pointer,
not the complete evidence for every statistic in the record. Consult the
cited location to assess the full contrast. Group definitions and numerical
fields retain the source extraction, while long quotations and extraction
work records are omitted.

## Provenance

`export_notes.json` records source file names, byte counts, SHA256 hashes,
modification timestamps, missing inputs, and export choices. Source paths
use neutral records-deposit labels. It contains no agent responses
or execution traces. `scripts/export_data_2026-11-12.py` recreates this export
from the records deposit and its benchmark code; it makes no API calls.
`--source-root` contains the deposit's `data/` directory. `--results-root`
contains `published_released_test.csv` and the other benchmark result files.
`--run` selects the verifier run and defaults to `final-2026-11-13`.
The reference-results exporter accepts the same parameter.

```sh
python scripts/export_data_2026-11-12.py --source-root RECORDS_DEPOSIT \
  --results-root BENCHMARK_RESULTS_FOLDER
```

The data compilation is licensed under CC BY 4.0, except the ComputAgeBench
derivatives described in [expert/README.md](expert/README.md). Short evidence
quotations remain attributable to the cited papers and are not relicensed by
this compilation.
