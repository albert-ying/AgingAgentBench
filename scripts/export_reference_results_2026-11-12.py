"""Export parsed benchmark predictions without copying responses or execution logs.

Run with --source-root pointing to the ClockBase records deposit.
Only selected numeric outputs and call metadata are written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

CALLS = {"higher": "higher", "lower": "lower", "none": "not significant", "ns": "not significant"}
FIELDS = ["record_id", "call", "direction", "p_value", "effect", "paper_id", "confidence", "source_system", "method", "row_ordinal", "n_case", "n_control", "recognizes_publication", "status"]


def load_json(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot proceed - required data file not found: {path}") from None
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Cannot read structured input {path.name}: {error}") from error


def load_lines(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot proceed - required data file not found: {path}") from None
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Cannot read structured input {path.name}: {error}") from error


def paper_key(record):
    source = record.get("source") or {}
    return str(next((source[k] for k in ("doi", "pmid", "pmcid", "citation", "url") if source.get(k)), record["id"]))


def numeric(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def alpha(record):
    value = record.get("threshold")
    if numeric(value) and 0 < value < 1:
        return float(value)
    if isinstance(value, str):
        found = re.fullmatch(r"\s*(?:[pP]\s*)?(?:<|<=|≤|=)?\s*(0?\.\d+|\d+(?:\.\d+)?[eE]-\d+)\s*", value)
        if found and 0 < float(found[1]) < 1:
            return float(found[1])
    return .05


def prediction(record, result, system, explicit_call=None):
    if not result or result.get("covered") is not True or result.get("direction") not in ("higher", "lower", "none"):
        return None
    sig = result.get("significant")
    if not isinstance(sig, bool):
        sig = result["p"] < alpha(record) if numeric(result.get("p")) else None
    called = explicit_call or (result["direction"] if sig is True and result["direction"] != "none" else "none" if sig is False else None)
    if called not in CALLS:
        called = None
    return {
        "record_id": record["id"], "call": CALLS.get(called, ""), "direction": result["direction"],
        "p_value": result.get("p") if numeric(result.get("p")) else None,
        "effect": result.get("mean_diff") if numeric(result.get("mean_diff")) else None,
        "paper_id": paper_key(record), "confidence": result.get("confidence"), "source_system": system,
        "method": result.get("method"), "row_ordinal": result.get("row_ordinal"),
        "n_case": result.get("n_case"), "n_control": result.get("n_control"),
        "recognizes_publication": result.get("recognizes_publication"),
        "status": "direction_only" if called is None else result.get("status"),
    }


def write_csv(path, rows, fields=None):
    try:
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields or FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, csv.Error) as error:
        raise RuntimeError(f"Cannot write {path}: {error}") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True,
                        help="Records deposit directory containing published_released_test.csv.")
    parser.add_argument("--out", type=Path, default=Path("reference_results"))
    args = parser.parse_args()
    base = args.source_root
    bench = base / "data/clockbase-benchmark-2026-10-05"
    results = args.results_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    final = {r["id"] for r in load_lines(bench / "ground_truth_t1_v2_final_2026-10-05.jsonl")}
    records = [r for name in ("t1-openai-002-s4", "t1new-openai-001-s4")
               for r in load_lines(bench / "runs" / name / "records.jsonl") if r["id"] in final]
    by_id = {r["id"]: r for r in records}
    assert len(records) == len(by_id) == 580
    names = {"S1": "clockbase_agent_stored", "S2": "clockbase_atlas_welch", "S3": "clockbase_paper_groups_welch"}
    for model in ("gpt-4.1", "gpt-5.5", "gpt-6-astra", "gpt-6-luna", "gpt-6-sol"):
        names[f"S4:openai:{model}"] = "language_model_" + model.replace("-", "_").replace(".", "_")
    exports = {}
    for system, name in names.items():
        exports[name] = [p for r in records if (p := prediction(r, r["systems"].get(system), system))]
    exports["constant_higher"] = [{"record_id": r["id"], "call": "higher", "direction": "higher",
                                    "paper_id": paper_key(r), "source_system": "S0"} for r in records]
    # The released test CSV is the final source of S3c and S3r calls.
    try:
        with (results / "published_released_test.csv").open(newline="") as handle:
            released = list(csv.DictReader(handle))
    except (OSError, csv.Error) as error:
        raise RuntimeError(f"Cannot read published test CSV: {error}") from error
    release_ids = {}
    for system, name in (("S3c", "clockbase_paper_groups"), ("S3r", "clockbase_paper_groups_individual_readers")):
        exports[name] = []
        for row in released:
            if not row.get(f"{system}_call"):
                continue
            result = {"covered": True, "p": float(row[f"{system}_p"]), "direction": row[f"{system}_direction"],
                      "method": row[f"{system}_method"], "n_case": row[f"{system}_n_case"], "n_control": row[f"{system}_n_control"]}
            pred = prediction(by_id[row["id"]], result, system, row[f"{system}_call"])
            if pred:
                exports[name].append(pred)
        release_ids[system] = {r["record_id"] for r in exports[name]}
    # Final verified atlas candidate, oriented to the published contrast.
    checks = {}
    for modality in ("dnam", "hs_rna", "mm_rna"):
        for row in load_lines(bench / "groupbench/design-checks/final-2026-11-12" / modality / "rows.jsonl"):
            checks[(modality, row["gse"], row["row_ordinal"])] = row
    modality_key = {"human DNAm": "dnam", "human RNA-seq": "hs_rna", "mouse RNA-seq": "mm_rna"}
    verified = []
    for r in records:
        s2 = r["systems"].get("S2", {})
        row = checks.get((modality_key[r["modality"]], r["gse"], s2.get("row_ordinal"))) if s2.get("covered") is True else None
        if row is None:
            result = dict(s2)
        else:
            result = {"covered": False}
            candidate = row["candidate"]
            if candidate["status"] == "OK" and numeric(candidate.get("p")):
                effect = -candidate["estimate"] if s2.get("swapped") else candidate["estimate"]
                result = {"covered": True, "direction": "higher" if effect > 0 else "lower" if effect < 0 else "none",
                          "p": candidate["p"], "mean_diff": effect, "method": candidate["method"], "row_ordinal": s2["row_ordinal"]}
        p = prediction(r, result, "S2c")
        if p:
            verified.append(p)
    exports["clockbase_atlas_verified"] = verified
    # Preserve the archived guard calculations rather than rerunning any models.
    guarded = {r["id"]: r for r in load_json(results / "auroc.json")["overflow_guard"]["recomputed"]}
    guarded_results = {}
    for r in records:
        result = dict(r["systems"].get("S3", {}))
        if r["id"] in guarded:
            mean, p = guarded[r["id"]]["after"]
            result.update(mean_diff=mean, p=p, significant=None, direction="higher" if mean > 0 else "lower" if mean < 0 else "none")
        guarded_results[r["id"]] = result
    exports["clockbase_paper_groups_guarded"] = [p for r in records if (p := prediction(r, guarded_results[r["id"]], "S3g"))]
    for pred in exports["clockbase_paper_groups_guarded"]:
        source_record = by_id[pred["record_id"]]
        # Only the age and age-acceleration measures have estimates in years.
        if source_record["modality"] == "human DNAm" and source_record["measure"] in ("age", "acceleration_difference", "acceleration_residual"):
            pred["effect_unit"] = "years"
    effect_pairs = []
    for r in records:
        effect = r.get("effect") or {}
        value = effect.get("value")
        if r["modality"] != "human DNAm" or not numeric(value) or not str(effect.get("unit", "")).lower().startswith("year"):
            continue
        if "uncertain" in str(effect.get("type", "")).lower():
            continue
        if r.get("direction") in ("higher", "lower") and value != 0 and (value > 0) != (r["direction"] == "higher"):
            continue
        result = guarded_results[r["id"]]
        if result.get("covered") is True and numeric(result.get("mean_diff")):
            effect_pairs.append({"record_id": r["id"], "paper_id": paper_key(r), "published_effect": value,
                                 "effect": result["mean_diff"], "unit": "years", "source_system": "S3g",
                                 "overflow_guard_applied": r["id"] in guarded})
    write_csv(out / "effect_pairs_years.csv", effect_pairs, ["record_id", "paper_id", "published_effect", "effect", "unit", "source_system", "overflow_guard_applied"])
    assert len(effect_pairs) == 30
    # Fixed intersections retain the exact paper comparison sets.
    common = set.intersection(release_ids["S3c"], release_ids["S3r"],
                              *({r["record_id"] for r in exports[n]} for s, n in names.items() if s.startswith("S4:")))
    cohorts = {"main110": sorted(common), "paper_groups_welch113": sorted(r["id"] for r in released), "atlas_shared93": sorted({r["record_id"] for r in verified if r["call"] and r["record_id"] in {x["record_id"] for x in exports["clockbase_atlas_welch"] if x["call"]} and by_id[r["record_id"]].get("significant") in (True, False)})}
    frameworks = (("codex", "scored-001"), ("claude_code", "scored-claude-001"), ("biomni", "scored-biomni-001"))
    for framework, folder in frameworks:
        reruns = load_lines(bench / "agentbench" / folder / "records.jsonl")
        cohorts.setdefault("agent_task158", sorted(r["id"] for r in reruns))
        own_sets = []
        systems = sorted({s for r in reruns for s in r["systems"] if s.startswith("R:")})
        for system in systems:
            model, kind = system.split(":")[1:]
            name = "agent_" + framework + "_" + model.replace("-", "_").replace(".", "_") + "_" + kind
            exports[name] = []
            for r in reruns:
                record = by_id[r["id"]]
                pred = prediction(record, r["systems"].get(system), system)
                if pred:
                    exports[name].append(pred)
            own_sets.append({r["record_id"] for r in exports[name]})
        own_sets.extend({r["id"] for r in reruns if r["systems"].get(system, {}).get("covered") is True and r["systems"][system].get("direction") in ("higher", "lower", "none")} for system in ("S1", "S2c"))
        cohorts["agent_shared_" + framework] = sorted(set.intersection(*own_sets))
    assert len(common) == 110
    assert len(cohorts["atlas_shared93"]) == 93
    # Expert agreement uses result-level ids distinct from published-paper ids.
    expert = load_lines(bench / "groupbench/design-checks/final-2026-11-12/a_result_stages.jsonl")
    expert_truth = []
    expert_out = {name: [] for name in ("agent", "released", "candidate")}
    for r in expert:
        if r["status"] != "ok" or r.get("expert_design_call") not in CALLS:
            continue
        rid = f"expert|{r['unit_id']}|{r['variant']}|{r['clock']}|{r['row_ordinal']}"
        stats = r.get("stats") or {}
        ref = stats.get("expert_design")
        method = r["expert_design_method"]
        test = {"Welch t-test (released)": "WELCH",
                "Welch t-test on subject means": "WELCH_UNIT_MEANS",
                "paired t-test on subject means": "PAIRED",
                "least squares on arm and age": "AGE_ADJUSTED",
                "least squares on arm and age, subject means": "AGE_ADJUSTED_UNIT_MEANS"}[method]
        expert_truth.append({"record_id": rid, "paper_id": r["gse"], "gse": r["gse"], "set": r["set"], "clock": r["clock"],
                             "published_call": CALLS[r["expert_design_call"]], "direction": "higher" if ref and ref[0] > 0 else "lower" if ref and ref[0] < 0 else "none",
                             "p_value": ref[1] if ref else None, "effect": ref[0] if ref else None,
                             "released": r.get("released", False), "label_unconfirmed": r.get("label_unconfirmed"), "final_class": r.get("final_class"),
                             "test": test, "method": method})
        for stage in expert_out:
            if stage != "agent" and not r.get("released"):
                continue
            pair = stats.get(stage)
            if not pair or r.get(stage + "_call") not in CALLS:
                continue
            pred = {"record_id": rid, "call": CALLS[r[stage + "_call"]], "direction": "higher" if pair[0] > 0 else "lower" if pair[0] < 0 else "none",
                    "p_value": pair[1], "effect": pair[0], "paper_id": r["gse"], "source_system": stage,
                    "method": r.get(stage + "_method"), "row_ordinal": r["row_ordinal"]}
            expert_out[stage].append(pred)
    write_csv(out / "expert_truth.csv", expert_truth, ["record_id", "paper_id", "gse", "set", "clock", "published_call", "direction", "p_value", "effect", "released", "label_unconfirmed", "final_class", "test", "method"])
    for stage, rows in expert_out.items():
        exports["expert_" + stage] = rows
    for name, rows in exports.items():
        write_csv(out / (name + ".csv"), rows,
                  FIELDS + ["effect_unit"] if name == "clockbase_paper_groups_guarded" else None)
    (out / "cohorts.json").write_text(json.dumps(cohorts, indent=2) + "\n")
    sources = [bench / "ground_truth_t1_v2_final_2026-10-05.jsonl", results / "published_released_test.csv", results / "auroc.json"]
    sources.extend(bench / "runs" / name / "records.jsonl" for name in ("t1-openai-002-s4", "t1new-openai-001-s4"))
    sources.extend(bench / "agentbench" / folder / "records.jsonl" for _, folder in frameworks)
    sources.extend(bench / "groupbench/design-checks/final-2026-11-12" / modality / "rows.jsonl" for modality in ("dnam", "hs_rna", "mm_rna"))
    sources.append(bench / "groupbench/design-checks/final-2026-11-12/a_result_stages.jsonl")
    notes = {"export_date": "2026-11-12", "inputs": [{"path": ("records deposit/benchmark/results/" + str(p.relative_to(results)) if p.is_relative_to(results) else "records deposit/" + str(p.relative_to(base))), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns} for p in sources],
             "files": {name + ".csv": {"records": len(rows), "calls": dict(Counter(r["call"] for r in rows))} for name, rows in exports.items()},
             "cohorts": {k: len(v) for k, v in cohorts.items()},
             "bootstrap": {"balanced_accuracy": {"replicates": 1000, "seed": 20261005, "unit": "paper"}, "direction_auroc_and_effect": {"replicates": 2000, "seed": 20261009, "unit": "paper"}},
             "notes": ["Only parsed predictions are exported. A missing row is an abstention or unavailable prediction, not a not-significant prediction. A blank call with status direction_only preserves an available direction without an inferential call.", "The S3c and S3r source CSV stores calls, directions and P values but not effect estimates. Their effect columns are empty.", "S3g effect pairs retain all 30 source numeric estimates. Four source predictions were recomputed after dropping clock outputs above 1000 years; source estimates and P values are preserved.", "The original three-way CI uses 1000 paper bootstraps; the finding AUROC and effect correlation use 2000.", "Expert results do not include unpublished annotation content or sample labels."]}
    (out / "export_notes.json").write_text(json.dumps(notes, indent=2) + "\n")
    expected = {"source_date": "2026-11-12", "three_way": load_json(results / "three_way_by_class.json")["systems"],
                "published_groups": load_json(results / "published_released_test.json")["systems"]}
    atlas_metrics = load_json(results / "auroc.json")
    expected["published_atlas"] = atlas_metrics["published"]
    expected["effect_years"] = atlas_metrics["effect_agreement_human_DNAm"]
    expected["expert_conclusions"] = load_json(results / "conclusion_stages.json")
    external = load_json(results / "external.json")
    expected["atlas_shared93"] = external["T1"]["shared_S2_S2c"]
    expected["atlas_gain"] = external["T1"]["paired_difference"]
    expected["reruns"] = {}
    for framework, folder in frameworks:
        stored = load_json(bench / "agentbench" / folder / "agent_reruns.json")
        expected["reruns"][framework] = {k: stored[k] for k in ("own_coverage", "shared_agent_systems", "model_with_and_without_data")}
    (out / "paper_metrics.json").write_text(json.dumps(expected, indent=2) + "\n")
    print(json.dumps({"prediction_files": len(exports), "cohorts": notes["cohorts"], "effect_pairs_years": len(effect_pairs), "expert_truth": len(expert_truth)}, indent=2))


if __name__ == "__main__":
    main()
