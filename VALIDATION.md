# Package validation

The test environment uses Python 3.12.13, NumPy 1.26.4, SciPy 1.11.4, and
pytest 9.2.0 on macOS arm64. The package supports Python 3.10 or later;
these checks used Python 3.12.

```sh
python -m pip wheel . --no-deps --no-build-isolation --no-index --no-cache-dir -w .venv/wheelcheck
python -m pytest -q
python scripts/reproduce_report_2026-11-12.py
```

The suite passes 67 tests with the wheel built. Without a wheel in
`.venv/wheelcheck`, the packaging test is skipped. Tests cover published
counts and bootstrap endpoints, all six agent reruns, expert orientation
subsets, user-supplied effects, direction requirements, CSV ground truth,
UTF-8 byte-order marks, prompt email redaction, answer-free tasks, and
bundled resources. Floating-point regression comparisons use an absolute
tolerance of 1e-14. All 159 clock-output files match their source SHA256 hashes.

The reproduction uses verifier run `final-2026-11-13`. It computes
85 published-system/cohort scores, 10 expert stage/orientation scores,
and 3 same-sample stage scores. All 528 numeric source comparisons pass.
Displayed cells are checked against the archived paper table as well as the
full-precision JSON fixtures. The source sampling universe is retained for
bootstrap intervals. The agent reruns retain their recorded atlas baseline.

The wheel is built offline using the existing environment. Its packaged
CSV and JSON resources are compared byte for byte with the current export.
Molecular preprocessing, source article extraction, and design-error
adjudication are outside these tests. Design-error counts and their adjusted
intervals are retained from the source analysis rather than refitted.
