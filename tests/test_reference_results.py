"""Regression checks against archived paper metrics, computed from shipped rows."""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

import pytest

from clockeffectbench.metrics import score_predictions

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference_results"
EXPECTED = json.loads((REF / "paper_metrics.json").read_text())
COHORTS = json.loads((REF / "cohorts.json").read_text())
MODEL_FILES = {
    "S0": "constant_higher",
    "S3": "clockbase_paper_groups_welch",
    "S3c": "clockbase_paper_groups",
    "S3r": "clockbase_paper_groups_individual_readers",
    "S4:openai:gpt-4.1": "language_model_gpt_4_1",
    "S4:openai:gpt-5.5": "language_model_gpt_5_5",
    "S4:openai:gpt-6-astra": "language_model_gpt_6_astra",
    "S4:openai:gpt-6-luna": "language_model_gpt_6_luna",
    "S4:openai:gpt-6-sol": "language_model_gpt_6_sol",
}


def csv_rows(filename):
    with (REF / (filename + ".csv")).open(newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(None)
def published_truth():
    return [json.loads(line) for line in (ROOT / "data/published.jsonl").read_text().splitlines()]


@lru_cache(None)
def scored(filename, cohort=None):
    return score_predictions(csv_rows(filename), published_truth(), record_ids=COHORTS[cohort] if cohort else None)


@pytest.mark.parametrize("system,filename", MODEL_FILES.items())
def test_three_way_published_counts_and_bootstrap(system, filename):
    actual = scored(filename, "main110")
    expected = EXPECTED["three_way"][system]
    assert actual["scored"] == 110
    assert actual["papers"] == 32
    assert actual["recall"] == {("not significant" if k == "none" else k): v for k, v in expected["recall"].items()}
    assert actual["balanced_accuracy"] == pytest.approx(expected["balanced_accuracy"], abs=1e-14)
    assert actual["balanced_accuracy_interval"] == pytest.approx(expected["balanced_accuracy_interval"], abs=1e-14)
    matrix = actual["confusion_matrix"]["values"]
    assert sum(sum(row) for row in matrix) == 110
    assert [matrix[i][i] for i in range(3)] == [expected["recall"][c][0] for c in ("lower", "higher", "none")]


@pytest.mark.parametrize("system,filename", [("S3c", "clockbase_paper_groups"), ("S3r", "clockbase_paper_groups_individual_readers"), ("S3", "clockbase_paper_groups_welch")])
def test_published_significance_and_direction(system, filename):
    actual = scored(filename, "main110") if system != "S3" else scored(filename, "paper_groups_welch113")
    expected = EXPECTED["published_groups"][system]
    # Welch also carries records without classifiable truth, which do not enter
    # the metric. The source finding block has exactly 113 classifiable rows.
    assert actual["direction_auroc"] == pytest.approx(expected["direction_auroc"], abs=1e-14)
    assert actual["direction_auroc_interval"] == pytest.approx(expected["direction_auroc_interval"], abs=1e-14)
    assert actual["same_direction_both_significant"] == expected["same_direction_both_significant"]
    assert actual["significant_in_published_direction"] == expected["replicated"]
    assert actual["direction_agreement"] == expected["sign_matches_significant"]
    k, n = expected["significant_only_in_clockbase"]
    assert actual["null_kept_null"] == [n-k, n]
    if system != "S3":
        assert actual["direction_agreement"] == [51, 52]
        assert actual["significant_in_published_direction"] == [40, 52]
        assert actual["significant_opposite"][0] == 0
        assert actual["null_kept_null"] == [51, 58]
    else:
        assert actual["significant_in_published_direction"] == [33, 54]


def test_verified_atlas_own_coverage_direction_auroc():
    actual = scored("clockbase_atlas_verified")
    expected = EXPECTED["published_atlas"]["human DNAm"]["S2c"]
    assert actual["scored"] == sum(expected["reference"].values())
    assert actual["same_direction_both_significant"] == [25, 26]
    assert actual["direction_auroc"] == pytest.approx(expected["direction_auroc"], abs=1e-14)
    assert actual["direction_auroc_interval"] == pytest.approx(expected["direction_auroc_interval"], abs=1e-14)


@pytest.mark.parametrize("system,filename", [("S2", "clockbase_atlas_welch"), ("S2c", "clockbase_atlas_verified")])
def test_atlas_shared_call_agreement(system, filename):
    actual = scored(filename, "atlas_shared92")
    expected = EXPECTED["atlas_shared92"]["metrics"][system]
    assert actual["scored"] == expected["call_n"]
    assert actual["call_agreement"] == pytest.approx(expected["call_agreement"], abs=1e-14)
    assert actual["balanced_accuracy"] == pytest.approx(expected["call_balanced_accuracy"], abs=1e-14)


RERUNS = [(framework, model, kind)
          for framework, models in (("codex", ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-5.5")),
                                    ("claude_code", ("claude-opus-5-5",)),
                                    ("biomni", ("gpt-6-astra",)))
          for model in models for kind in ("raw", "recomputed")]


@pytest.mark.parametrize("framework,model,kind", RERUNS)
def test_agent_rerun_calls_directions_and_auroc(framework, model, kind):
    filename = "agent_" + framework + "_" + model.replace("-", "_").replace(".", "_") + "_" + kind
    actual = scored(filename, "agent_task158")
    expected = EXPECTED["reruns"][framework]["own_coverage"][f"R:{model}:{kind}"]
    assert actual["scored"] == expected["call_n"]
    assert actual["call_agreement"] == pytest.approx(expected["call_agreement"], abs=1e-14)
    k, n = actual["direction_agreement"]
    assert n == expected["direction_n"]
    assert k / n == pytest.approx(expected["direction_agreement"], abs=1e-14)
    assert actual["direction_auroc"] == pytest.approx(expected["findings"]["direction_auroc"], abs=1e-14)
    assert actual["direction_auroc_interval"] == pytest.approx(expected["findings"]["direction_auroc_interval"], abs=1e-14)
    assert actual["balanced_accuracy_interval"] == pytest.approx(expected["call_balanced_accuracy_interval"], abs=1e-14)


@pytest.mark.parametrize("set_name,confirmed", [("A1", False), ("A2", False), ("A2", True)])
def test_expert_candidate_call_agreement(set_name, confirmed):
    expected = EXPECTED["expert_conclusions"][set_name]["expert_design_call"]["candidate_call"]["labels confirmed" if confirmed else "all released rows"]
    n = expected["units"]
    k = n - expected["errors"]
    truth = csv_rows("expert_truth")
    selected = [r["record_id"] for r in truth if r["set"] == set_name and (not confirmed or r["label_unconfirmed"] == "False")]
    actual = score_predictions(csv_rows("expert_candidate"), truth, record_ids=selected)
    assert actual["scored"] == n
    assert actual["call_agreement"] == k / n
    assert actual["significant_opposite"][0] == 0


@pytest.mark.parametrize("set_name,opposite", [("A1", 1), ("A2", 10)])
def test_expert_agent_opposite_significant_calls(set_name, opposite):
    truth = csv_rows("expert_truth")
    selected = [r["record_id"] for r in truth if r["set"] == set_name]
    actual = score_predictions(csv_rows("expert_agent"), truth, record_ids=selected)
    assert actual["significant_opposite"][0] == opposite


def test_effect_pairs_in_years():
    from clockeffectbench.metrics import score_effects
    actual = score_effects(csv_rows("effect_pairs_years"))
    expected = EXPECTED["effect_years"]["S3g"]
    assert actual["pairs"] == expected["pairs"] == 30
    assert actual["papers"] == expected["papers"] == 7
    assert actual["spearman"] == pytest.approx(expected["spearman"], abs=1e-14)
    assert actual["spearman_interval"] == pytest.approx(expected["spearman_interval"], abs=1e-14)
    assert actual["median_absolute_difference"] == pytest.approx(expected["median_absolute_difference_years"], abs=1e-14)


def test_paired_atlas_call_gain():
    from clockeffectbench.metrics import compare_calls
    actual = compare_calls(csv_rows("clockbase_atlas_welch"), csv_rows("clockbase_atlas_verified"), published_truth())
    expected = EXPECTED["atlas_gain"]
    assert actual["scored"] == EXPECTED["external"]["T1"]["shared_S2_S2c"]["metrics"]["S2c"]["call_n"]
    assert actual["common_records"] == EXPECTED["external"]["T1"]["shared_S2_S2c"]["records"]
    assert actual["difference"] == expected["call_agreement_S2c_minus_S2"]
    assert actual["interval"] == pytest.approx(expected["interval"], abs=1e-14)
