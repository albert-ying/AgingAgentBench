"""Command line, input validation, and shipped data integrity checks."""
import hashlib
import json
from pathlib import Path

import pytest

from clockeffectbench.cli import main
from clockeffectbench.io import read_rows
from clockeffectbench.metrics import score_predictions

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / "reference_results/paper_metrics.json").read_text())


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
    # The released-test predictions have no effect estimates.
    assert printed["effect_years"]["pairs"] == 0
    assert printed["effect_cohort"]["source"] == "predictions"


def test_cli_expert_subset(tmp_path, capsys):
    main(["score", "--expert", "--expert-set", "human-confirmed",
          "--predictions", str(ROOT / "reference_results/expert_candidate.csv"),
          "--output", str(tmp_path / "expert.json")])
    result = json.loads(capsys.readouterr().out)
    expected = EXPECTED["expert_conclusions"]["A2"]["expert_design_call"]["candidate_call"]["labels confirmed"]
    assert result["scored"] == expected["units"]
    assert result["call_agreement"] == (expected["units"] - expected["errors"]) / expected["units"]


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


def test_public_expert_groups_cover_every_frozen_reference():
    truth = read_rows(ROOT / "reference_results/expert_truth.csv")
    for set_, name, count in [("A1", "mouse_rna_groups", 98), ("A2", "human_dnam_groups", 50)]:
        groups = read_rows(ROOT / "data/expert" / (name + ".jsonl"))
        assert len(groups) == count
        keys = {(r["unit_id"], str(r["variant"])) for r in groups}
        for row in truth:
            if row["set"] == set_:
                assert tuple(row["record_id"].split("|")[1:3]) in keys
        assert all(r["case_gsms"] and r["control_gsms"] for r in groups)
        assert all(not set(r["case_gsms"]) & set(r["control_gsms"]) for r in groups)


def test_s18_released_test_matches_computed_auroc():
    table = read_rows(ROOT / "reference_results/supplementary_table_s18.csv")
    row = next(r for r in table if r["reference"] == "Published results" and r["measure"] == "Direction AUROC"
               and r["stage"] == "Paper's groups, released test")
    assert float(row["estimate"]) == pytest.approx(round(EXPECTED["published_groups"]["S3c"]["direction_auroc"], 4), abs=1e-14)
    assert float(row["ci_low"]) == pytest.approx(round(EXPECTED["published_groups"]["S3c"]["direction_auroc_interval"][0], 4), abs=1e-14)


def test_s18_expert_conclusions_match_source_counts():
    rows = read_rows(ROOT / "reference_results/supplementary_table_s18.csv")
    stages = {"Raw agent": "agent_call", "Verifier, Welch test only": "released_call", "Released": "candidate_call"}
    for row in rows:
        if row["reference"] != "Expert-defined groups" or row["measure"] != "Conclusion agrees (direction and significance)":
            continue
        set_name = "A1" if row["modality"] == "Mouse RNA-seq" else "A2"
        stage = stages[row["stage"]]
        stratum = ("all rows of the agent" if stage == "agent_call" else
                   "labels confirmed" if row["note"].startswith("labels confirmed;") else "all released rows")
        expected = EXPECTED["expert_conclusions"][set_name]["expert_design_call"][stage][stratum]
        assert int(row["numerator"]) == expected["units"] - expected["errors"]
        assert int(row["denominator"]) == expected["units"]


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
        assert "clockeffectbench/data/tasks.jsonl" in names
        assert "clockeffectbench/reference_results/cohorts.json" in names
        assert len([n for n in names if n.startswith("clockeffectbench/data/clockbase_outputs/") and n.endswith(".csv")]) == 159
        for folder in ("data", "reference_results"):
            for path in (ROOT / folder).rglob("*"):
                if path.is_file() and path.suffix in (".csv", ".json", ".jsonl"):
                    member = "clockeffectbench/" + str(path.relative_to(ROOT))
                    # Reproduction results are generated after the wheel check.
                    if path.name != "reproduced_metrics.json":
                        assert archive.read(member) == path.read_bytes(), member


def test_effect_selection_uses_submitted_estimates(tmp_path, capsys, truth):
    """Selecting reference IDs must never copy their estimates into a score."""
    import numpy as np
    pairs = read_rows(ROOT / "reference_results/effect_pairs_years.csv")
    selected = {r["record_id"] for r in pairs}
    # Submitted estimates deliberately differ from ClockBase and include one
    # eligible result outside the paper's effect subset.
    records = [r for r in truth if r["record_id"] in selected]
    from clockeffectbench.metrics import effect_pair
    extra = next(r for r in truth if r["record_id"] not in selected
                 and effect_pair(r, {"effect": 2, "effect_unit": "years"}))
    predictions = [{"record_id": r["record_id"], "call": "higher", "effect": 2,
                    "effect_unit": "years"} for r in records + [extra]]
    source = tmp_path / "own.jsonl"
    source.write_text("".join(json.dumps(r) + "\n" for r in predictions))
    main(["score", "--predictions", str(source), "--cohort", "main110",
          "--effects", str(ROOT / "reference_results/effect_pairs_years.csv"),
          "--output", str(tmp_path / "own_scores.json")])
    result = json.loads(capsys.readouterr().out)
    assert result["effect_years"]["pairs"] == 30
    assert result["effect_years"]["spearman"] is None
    assert result["effect_years"]["median_absolute_difference"] == float(
        np.median([abs(float(r["published_effect"]) - 2) for r in pairs]))


def test_guarded_effect_cli_reproduces_paper(tmp_path, capsys):
    main(["score", "--predictions", str(ROOT / "reference_results/clockbase_paper_groups_guarded.csv"),
          "--effects", str(ROOT / "reference_results/effect_pairs_years.csv"),
          "--output", str(tmp_path / "guarded.json")])
    result = json.loads(capsys.readouterr().out)["effect_years"]
    expected = json.loads((ROOT / "reference_results/paper_metrics.json").read_text())["effect_years"]["S3g"]
    assert result["pairs"] == expected["pairs"] == 30
    assert result["spearman"] == pytest.approx(expected["spearman"], abs=1e-14)
    assert result["spearman_interval"] == pytest.approx(expected["spearman_interval"], abs=1e-14)
    assert result["median_absolute_difference"] == pytest.approx(expected["median_absolute_difference_years"], abs=1e-14)


def test_nonsignificant_p_value_requires_direction(truth):
    predictions = read_rows(ROOT / "reference_results/clockbase_paper_groups.csv")
    for row in predictions:
        row.pop("direction")
    with pytest.raises(ValueError, match="direction or signed effect is required"):
        score_predictions(predictions, truth)


@pytest.mark.parametrize("effect,direction", [(2, "higher"), (-2, "lower"), (0, "none")])
def test_nonsignificant_signed_effect_supplies_direction(truth, effect, direction):
    record = next(r for r in truth if r["published_call"] == "higher")
    result = score_predictions([{"record_id": record["record_id"], "call": "not significant",
                                 "effect": effect, "p_value": .2}], truth, [record["record_id"]])
    assert result["direction_agreement"] == [int(direction == "higher"), 1]
    assert result["auroc_significant_records"] == 1


def test_direction_only_answers_enter_auroc(truth):
    records = [next(r for r in truth if r["published_call"] == c) for c in ("lower", "higher")]
    result = score_predictions([{"record_id": r["record_id"], "direction": r["direction"],
                                 "p_value": .01} for r in records], truth,
                               [r["record_id"] for r in records])
    assert result["scored"] == 0
    assert result["auroc_significant_records"] == 2
    assert result["direction_agreement"] == [2, 2]
    assert result["direction_auroc"] == 1


def test_csv_truth_matches_jsonl_scores(tmp_path, capsys):
    csv_truth = read_rows(ROOT / "data/published.csv")
    json_truth = read_rows(ROOT / "data/published.jsonl")
    for csv_row, json_row in zip(csv_truth, json_truth):
        for key in ("source", "effect", "case_gsms", "control_gsms", "covariates", "eligibility", "significant"):
            assert (csv_row[key] or None) == (json_row[key] or None)
    results = []
    for suffix in ("csv", "jsonl"):
        main(["score", "--predictions", str(ROOT / "reference_results/clockbase_paper_groups_guarded.csv"),
              "--ground-truth", str(ROOT / "data" / ("published." + suffix)),
              "--effects", str(ROOT / "reference_results/effect_pairs_years.csv"),
              "--output", str(tmp_path / (suffix + ".json"))])
        results.append(json.loads(capsys.readouterr().out))
    assert results[0] == results[1]
    assert results[0]["effect_years"]["pairs"] == 30


@pytest.mark.parametrize("suffix", ["csv", "jsonl"])
def test_bom_input_is_accepted(suffix, tmp_path, capsys, prediction):
    path = tmp_path / ("excel." + suffix)
    content = (f"record_id,call\n{prediction['record_id']},higher\n" if suffix == "csv" else
               json.dumps({"record_id": prediction["record_id"], "call": "higher"}) + "\n")
    path.write_text(content, encoding="utf-8-sig")
    main(["score", "--predictions", str(path), "--output", str(tmp_path / "score.json")])
    assert json.loads(capsys.readouterr().out)["scored"] == 1


def test_tasks_exclude_outcomes(truth):
    tasks = read_rows(ROOT / "data/tasks.jsonl")
    allowed = {"record_id", "gse", "modality", "clock_reported", "clock_clockbase", "measure",
               "case_label", "control_label", "case_definition", "control_definition",
               "case_gsms", "control_gsms", "threshold"}
    assert len(tasks) == 580
    assert {r["record_id"] for r in tasks} == {r["record_id"] for r in truth}
    assert all(set(r) == allowed for r in tasks)


def test_geo_email_redaction():
    from clockeffectbench.prompts import EMAIL, redact_emails
    prompts = read_rows(ROOT / "data/prompts.jsonl")
    assert not any(EMAIL.search(r["prompt"]) for r in prompts)
    redacted = [r for r in prompts if "geo_email_redacted" in r["flags"]]
    assert len(redacted) == 2
    assert all("[email removed]" in r["prompt"] for r in redacted)
    assert redact_emails("Contact person@example.org") == "Contact [email removed]"


def test_missing_frozen_prompt_does_not_promise_study_fallback(capsys):
    with pytest.raises(SystemExit) as error:
        main(["prompt", "MED-34341706-GSE53740-other-0"])
    assert error.value.code == 2
    message = capsys.readouterr().err
    assert "324 records" in message
    assert "provide --study" not in message


def test_expert_truth_preserves_source_methods():
    from collections import Counter
    rows = read_rows(ROOT / "reference_results/expert_truth.csv")
    assert Counter(r["test"] for r in rows) == EXPECTED["expert_reference_methods"]
    assert all(r["method"] for r in rows)


def test_mouse_confirmed_orientation(tmp_path, capsys):
    main(["score", "--expert", "--expert-set", "mouse-confirmed",
          "--predictions", str(ROOT / "reference_results/expert_candidate.csv"),
          "--output", str(tmp_path / "expert.json")])
    result = json.loads(capsys.readouterr().out)
    assert result["scored"] == 87
    assert result["call_agreement"] == 86 / 87
