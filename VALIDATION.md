# Package validation

The test environment uses Python 3.12.13, NumPy 1.26.4, SciPy 1.11.4, and
pytest 9.2.0 on macOS arm64. The package supports Python 3.10 or later;
these checks used Python 3.12.

```sh
python -m pip wheel . --no-deps --no-build-isolation -w .venv/wheelcheck
python -m pytest -q
python scripts/reproduce_report_2026-11-12.py
```

The suite passes 66 tests with the wheel built. Without a wheel in
`.venv/wheelcheck`, the packaging test is skipped. Tests cover published
counts and bootstrap endpoints, all six agent reruns, expert orientation
subsets, user-supplied effects, direction requirements, CSV ground truth,
UTF-8 byte-order marks, prompt email redaction, answer-free tasks, and
bundled resources. Floating-point regression comparisons use an absolute
tolerance of 1e-14. All 159 clock-output files match their source SHA256 hashes.

The reproduction report computes 39 published-system/cohort scores and four
expert orientation subsets. Published metric values match the archived source
fixtures; molecular preprocessing and original article extraction are outside
these tests.
