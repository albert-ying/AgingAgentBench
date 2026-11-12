"""Command line, input validation, and shipped data integrity checks."""
import hashlib
import json
from pathlib import Path

import pytest

from clockeffectbench.cli import main
from clockeffectbench.io import read_rows
from clockeffectbench.metrics import score_predictions

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def truth():
    return read_rows(ROOT / "data/published.jsonl")


@pytest.fixture
def prediction():
    return read_rows(ROOT / "reference_results/clockbase_paper_groups.csv")[0]


@pytest.mark.parametrize("changes,error", [
    ({"record_id": "unknown-record"}, "Unknown record_id"),
    ({"call": "maybe"}, "Invalid call"),
    ({"p_value": "nan"}, "must be finite"),
    ({"p_value": "1.1"}, "outside"),
    ({"effect": "-2", "direction": "higher"}, "Effect contradicts"),
    ({"call": "lower", "direction": "higher"}, "Call contradicts"),
    ({"call": "", "direction": "", "effect": ""}, "call or direction"),
])
def test_invalid_predictions_are_rejected(truth, prediction, changes, error):
    prediction.update(changes)
    with pytest.raises(ValueError, match=error):
        score_predictions([prediction], truth)


def test_duplicate_predictions_are_rejected(truth, prediction):
    with pytest.raises(ValueError, match="Duplicate record_id"):
        score_predictions([prediction, prediction], truth)


def test_cli_writes_scores(tmp_path, capsys):
    output = tmp_path / "scores.json"
    main(["score", "--predictions", str(ROOT / "reference_results/clockbase_paper_groups.csv"),
          "--cohort", "main110", "--effects", str(ROOT / "reference_results/effect_pairs_years.csv"),
          "--output", str(output)])
    printed = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text()) == printed
    assert printed["recall"]["lower"] == [10, 16]
    assert printed["effect_years"]["pairs"] == 30


def test_cli_expert_subset(tmp_path, capsys):
    main(["score", "--expert", "--expert-set", "human-confirmed",
          "--predictions", str(ROOT / "reference_results/expert_candidate.csv"),
          "--output", str(tmp_path / "expert.json")])
    result = json.loads(capsys.readouterr().out)
    assert result["scored"] == 128
    assert result["call_agreement"] == 126/128


def test_prompt_matches_frozen_input(capsys):
    row = read_rows(ROOT / "data/prompts.jsonl")[0]
    main(["prompt", row["record_id"]])
    assert capsys.readouterr().out == row["prompt"] + "\n"


def test_missing_input_has_required_message(capsys, tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["score", "--predictions", str(tmp_path / "absent.csv")])
    assert error.value.code == 2
    assert "Cannot proceed - required data file not found:" in capsys.readouterr().err


def test_published_records_and_clock_output_hashes(truth):
    assert len(truth) == len({r["record_id"] for r in truth}) == 580
    assert len({r["paper_id"] for r in truth}) == 93
    assert len({r["gse"] for r in truth}) == 125
    for row in truth:
        assert row["source"]["first_author"]
        assert row["source"]["year"]
        assert 0 < len(row["source"]["quote"].split()) <= 25
        assert not set(row["case_gsms"]) & set(row["control_gsms"])
        if row["significant"] is None:
            assert row["published_call"] is None
    manifest = json.loads((ROOT / "data/clockbase_outputs/manifest.json").read_text())
    assert len(manifest) == 159
    assert sum(row["bytes"] for row in manifest) == 12_848_572
    for row in manifest:
        content = (ROOT / "data/clockbase_outputs" / row["file"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == row["sha256"] == row["atlas_expected_sha256"]


def test_all_main_prompts_available():
    prompts = read_rows(ROOT / "data/prompts.jsonl")
    assert len(prompts) == len({r["record_id"] for r in prompts}) == 324
    common = json.loads((ROOT / "reference_results/cohorts.json").read_text())["main110"]
    assert set(common) <= {r["record_id"] for r in prompts}


def test_s18_released_test_matches_computed_auroc():
    table = read_rows(ROOT / "reference_results/supplementary_table_s18.csv")
    row = next(r for r in table if r["reference"] == "Published results" and r["measure"] == "Direction AUROC"
               and r["stage"] == "Paper's groups, released test")
    assert float(row["estimate"]) == pytest.approx(round(0.9965277777777778, 4), abs=1e-14)
    assert float(row["ci_low"]) == pytest.approx(round(0.9809523809523809, 4), abs=1e-14)


def test_wheel_contains_runtime_data_when_available():
    # Building a wheel is a packaging check, independent of the scientific tests.
    from zipfile import ZipFile
    wheels = list((ROOT / ".venv/wheelcheck").glob("clockeffectbench-*.whl"))
    if not wheels:
        pytest.skip("No locally built wheel supplied for the optional packaging check")
    with ZipFile(wheels[-1]) as archive:
        names = set(archive.namelist())
        assert "clockeffectbench/data/published.jsonl" in names
        assert "clockeffectbench/data/prompts.jsonl" in names
        assert "clockeffectbench/reference_results/cohorts.json" in names
        assert len([n for n in names if n.startswith("clockeffectbench/data/clockbase_outputs/") and n.endswith(".csv")]) == 159
