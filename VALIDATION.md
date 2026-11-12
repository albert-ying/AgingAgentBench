# Local validation

Validation completed on November 12, 2026. The test environment is the fresh,
isolated `.venv` inside this repository, with Python 3.12.13, NumPy 1.26.4,
pandas 2.2.3, SciPy 1.11.4, and pytest 9.2.0. The supported Python floor is
3.10; this session exercised Python 3.12.

## Executed checks

The scientific regression suite and command-line checks pass locally.

- `python -m pytest -q`: 51 passed.
- Editable installation succeeds without network access or build isolation.
- The installed CLI prints and writes the main110 scores with the separate
  year-effect cohort and scores the confirmed human expert subset.
- The prompt command reproduces a frozen baseline input. All 110 shared
  records have a frozen prompt among the 324 shipped inputs.
- A built wheel contains the data, reference predictions, and clock outputs.
  An isolated import from the installed wheel, outside the checkout's import
  path, loads the bundled records and reproduces the main110 score.
- All 159 per-sample clock tables match their released-atlas SHA256 values.
  Every frozen expert comparison has a corresponding public-source group
  definition among 98 mouse and 50 human definitions.
- Source fixtures and recomputed metrics are separate files. Tests compare
  integer counts exactly and floating results to absolute tolerance 1e-14,
  including the published bootstrap endpoints.
- Heading checks report no violations. The two single-heading license and
  clock-output notes were reviewed and retained as short documents.

The first dependency install failed with a proxy 403 response. Automatic
approval review rejected the escalation with "approval request failed".
Dependencies were then installed into the fresh `.venv` offline from
packages already present in the source environment. No network access is
needed for the installed scoring commands.

## Analysis checks

The final review was performed within this session. It used the scientific
analysis review checklist and made no second-model calls.

| Check | Evidence and limit |
| --- | --- |
| Execution integrity | Source rows were read and exported; unique identifiers, sample-arm overlap, missing files, clock-table hashes, and CLI outputs were checked. |
| Numerical verification | Shipped predictions reproduce the primary counts, AUROC, bootstrap intervals, year-effect correlation, six reruns, and expert agreement. The original test selections and molecular predictions were not recomputed. |
| Logical interpretation | Agreement measures recovery of published clock results and expert-group calls. It does not establish intervention efficacy or lifespan effects. |
| Scope | The repository contains local data, parsed predictions, scoring, prompts, tests, provenance, and documentation. It does not run analysis agents or publish results. |
| Source attribution | Empirical values come from the named source files with hashes and timestamps. No simulations or imputed empirical values were introduced. The 580 original article extractions were not independently repeated. |
| Scientific assumptions | Source thresholds, orientations, eligibility, and paper clustering are retained. The manuscript's RNA modality wording differs from the source labels, as recorded in REPORT.md. |
| Reproducibility | Seeds, replicate counts, source fixtures, export scripts, and package versions are recorded. The public mouse annotation's unstated reuse terms remain a release decision. |

The benchmark performance claims are reproduced. The remaining source and
licensing questions are listed in [REPORT.md](REPORT.md).

## Repository hygiene

The release files were scanned for absolute local paths, server paths,
credential patterns, private keys, and environment files. No such content
was found. No raw model responses, ledgers, or agent traces are included.
All release files are below 50 MB. `.venv`, generated scores, wheel builds,
and local memory are ignored. Source directories were read only.

The 233 release files total 19,523,770 bytes (19.52 MB), excluding `.git` and `.venv`. The largest file is 1,774,246 bytes. The per-sample clock tables account for 12,848,572 bytes. Git metadata is about 7.2 MiB and the ignored test environment about 377 MiB before the final documentation commit.

## Local commits

The commits use Kejun Albert Ying's attribution and contain no coauthor
trailers. No commit was pushed.

| Revision | Message |
| --- | --- |
| `5b8bcc1` | Start the standalone ClockEffectBench repository |
| `e7db661` | Add published contrasts and portable benchmark data |
| `f0f4478` | Add scoring commands and reproduce the paper reference results |
| `HEAD` | Document benchmark use and public annotation provenance |

The last row identifies the documentation commit containing this file.
