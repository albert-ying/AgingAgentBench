"""Recompute benchmark metrics and check them against archived paper sources."""
from collections import Counter
from importlib.metadata import version
import json
import math
import platform
from pathlib import Path

import numpy as np

from clockeffectbench.io import read_rows, write_json
from clockeffectbench.metrics import bootstrap, compare_calls, score_effects, score_predictions

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference_results"
SYSTEM_FILES = {
    "S0": "constant_higher", "S1": "clockbase_agent_stored",
    "S2": "clockbase_atlas_welch", "S2c": "clockbase_atlas_verified",
    "S3": "clockbase_paper_groups_welch", "S3c": "clockbase_paper_groups",
    "S3r": "clockbase_paper_groups_individual_readers",
}
for model in ("gpt-4.1", "gpt-5.5", "gpt-6-astra", "gpt-6-luna", "gpt-6-sol"):
    SYSTEM_FILES["S4:openai:" + model] = "language_model_" + model.replace("-", "_").replace(".", "_")


def same_sample_metrics(rows, stage, settings):
    items = [{"paper_id": r["paper_id"], "truth": r["published_call"], "call": r[stage]} for r in rows]

    def agreement(sample):
        return sum(r["truth"] == r["call"] for r in sample) / len(sample) if sample else None

    def kappa(sample):
        if not sample:
            return None
        a, b = Counter(r["truth"] for r in sample), Counter(r["call"] for r in sample)
        chance = sum(a[c] * b[c] for c in ("higher", "lower", "none")) / len(sample) ** 2
        return (agreement(sample) - chance) / (1 - chance) if chance < 1 else None

    return {"n": len(items), "call_agreement": agreement(items), "kappa": kappa(items),
            **{key + "_interval": bootstrap(items, statistic, settings["replicates"], settings["seed"])
               for key, statistic in (("call_agreement", agreement), ("kappa", kappa))}}


def main():
    try:
        truth = read_rows(ROOT / "data/published.jsonl")
        cohorts = json.loads((REF / "cohorts.json").read_text())
        expected = json.loads((REF / "paper_metrics.json").read_text())
        notes = json.loads((ROOT / "data/export_notes.json").read_text())
        results, checks = {}, []

        def check(name, actual, source):
            def equal(a, b):
                if isinstance(b, dict):
                    return isinstance(a, dict) and all(k in a and equal(a[k], v) for k, v in b.items())
                if isinstance(b, (list, tuple)):
                    return isinstance(a, (list, tuple)) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
                if isinstance(b, float):
                    return isinstance(a, (float, int)) and math.isclose(a, b, rel_tol=0, abs_tol=1e-14)
                return a == b
            if not equal(actual, source):
                raise ValueError(f"Source metric mismatch for {name}: computed {actual!r}; source {source!r}")
            checks.append({"metric": name, "computed": actual, "source": source})

        def compute(name, cohort=None):
            key = name + ("@" + cohort if cohort else "")
            if key not in results:
                results[key] = score_predictions(read_rows(REF / (name + ".csv")), truth,
                                                cohorts[cohort] if cohort else None)
            return results[key]

        def source_scores(label, value, source):
            check(label + ".scored", value["scored"], source["call_n"])
            check(label + ".call_agreement", value["call_agreement"], source["call_agreement"])
            check(label + ".balanced_accuracy", value["balanced_accuracy"], source["call_balanced_accuracy"])
            check(label + ".balanced_accuracy_interval", value["balanced_accuracy_interval"], source["call_balanced_accuracy_interval"])
            k, n = value["direction_agreement"]
            check(label + ".direction_n", n, source["direction_n"])
            check(label + ".direction_agreement", k / n if n else None, source["direction_agreement"])

        ratio = lambda pair: f"{pair[0]}/{pair[1]}"
        interval = lambda value, bounds: f"{value:.4f} [{bounds[0]:.4f}, {bounds[1]:.4f}]"
        lines = ["# ClockEffectBench reproduction", "",
                 f"Source run `{notes['verifier_run']}`. The scorer reads the shipped predictions",
                 "and compares the results with independently archived source metrics.",
                 "The paper's source table is retained in [paper_table.md](reference_results/paper_table.md).",
                 "Full precision results and source comparisons are in",
                 "`reference_results/reproduced_metrics.json`.", "", "## Published paper groups", "",
                 "This comparison uses the paper's assigned groups. It is distinct from the",
                 "released atlas-row comparison in the paper's summary table.", "",
                 "| System | Lower | Higher | Null | Balanced accuracy with interval |",
                 "| --- | --- | --- | --- | --- |"]
        for system, source in expected["three_way"].items():
            value = compute(SYSTEM_FILES[system], "main110")
            check(system + ".main.recall", value["recall"], {"not significant" if k == "none" else k: v for k, v in source["recall"].items()})
            for key in ("balanced_accuracy", "balanced_accuracy_interval"):
                check(system + ".main." + key, value[key], source[key])
            lines.append(f"| {system} | {ratio(value['recall']['lower'])} | {ratio(value['recall']['higher'])} | {ratio(value['recall']['not significant'])} | {interval(value['balanced_accuracy'], value['balanced_accuracy_interval'])} |")
        lines += ["", "| System | Significant in published direction | Direction agreement | Direction AUROC with interval |",
                  "| --- | --- | --- | --- |"]
        for system, source in expected["published_groups"].items():
            value = compute(SYSTEM_FILES[system], "paper_groups_welch113" if system == "S3" else "main110")
            for key in ("direction_auroc", "direction_auroc_interval", "same_direction_both_significant"):
                check(system + ".findings." + key, value[key], source[key])
            check(system + ".replicated", value["significant_in_published_direction"], source["replicated"])
            check(system + ".sign", value["direction_agreement"], source["sign_matches_significant"])
            lines.append(f"| {system} | {ratio(value['significant_in_published_direction'])} | {ratio(value['direction_agreement'])} | {interval(value['direction_auroc'], value['direction_auroc_interval'])} |")

        lines += ["", "## Published atlas rows", "",
                  "All cohorts preserve the source sampling universe, including rows without",
                  "classifiable outcomes. Parentheses give the number of scored calls.", "",
                  "| Cohort | System | Call agreement | Direction agreement | Balanced accuracy with interval |",
                  "| --- | --- | --- | --- | --- |"]
        ext = expected["external"]["T1"]
        for block, cohort in (("own_coverage", None), ("shared_S1_S2_S2c", "atlas_agent_shared"),
                              ("shared_S2_S2c", "atlas_shared_covered"), ("candidate_estimand_applied", "atlas_estimand_applied")):
            sources = ext[block] if cohort is None else ext[block]["metrics"]
            for system, source in sources.items():
                value = compute(SYSTEM_FILES[system], cohort)
                source_scores(block + "." + system, value, source)
                lines.append(f"| {block} | {system} | {100*value['call_agreement']:.2f}% ({value['scored']}) | {ratio(value['direction_agreement'])} | {interval(value['balanced_accuracy'], value['balanced_accuracy_interval'])} |")
        atlas = compute(SYSTEM_FILES["S2c"])
        atlas_source = expected["published_atlas"]["human DNAm"]["S2c"]
        for key in ("direction_auroc", "direction_auroc_interval", "same_direction_both_significant"):
            check("atlas." + key, atlas[key], atlas_source[key])
        atlas_key = next(k for k in cohorts if k.startswith("atlas_shared") and k.removeprefix("atlas_shared").isdigit())
        for system in ("S2", "S2c"):
            value = compute(SYSTEM_FILES[system], atlas_key)
            source = expected[atlas_key]["metrics"][system]
            check(atlas_key + "." + system + ".call", value["call_agreement"], source["call_agreement"])
        gain = compare_calls(read_rows(REF / "clockbase_atlas_welch.csv"), read_rows(REF / "clockbase_atlas_verified.csv"), truth)
        check("atlas.gain", gain["difference"], expected["atlas_gain"]["call_agreement_S2c_minus_S2"])
        check("atlas.gain_interval", gain["interval"], expected["atlas_gain"]["interval"])
        lines += ["", f"The paired atlas gain is {interval(100*gain['difference'], [100*v for v in gain['interval']])} percentage points",
                  f"across {gain['common_records']} shared covered records. Atlas direction AUROC is",
                  interval(atlas["direction_auroc"], atlas["direction_auroc_interval"]) + ".", "",
                  "## Paper language-model cohort", "",
                  "This cohort is the comparison with models given the paper description in the",
                  "summary table. It uses the earlier paper-group Welch analysis.", "",
                  "| System | Scored calls | Balanced accuracy with interval | Direction agreement |",
                  "| --- | --- | --- | --- |"]
        for system, source in expected["paper_models_shared"]["metrics"].items():
            value = compute(SYSTEM_FILES[system], "paper_models_shared")
            source_scores("paper_models_shared." + system, value, source)
            lines.append(f"| {system} | {value['scored']} | {interval(value['balanced_accuracy'], value['balanced_accuracy_interval'])} | {ratio(value['direction_agreement'])} |")

        lines += ["", "## Same-sample comparisons", "",
                  "Calls and Cohen's kappa are recomputed from the exported matched contrasts.", "",
                  "| Stage | Contrasts | Call agreement | Kappa with interval |",
                  "| --- | --- | --- | --- |"]
        same_samples = {}
        for stage in ("agent", "released", "candidate"):
            value = same_sample_metrics(read_rows(REF / "same_sample_calls.csv"), stage, expected["same_sample_bootstrap"])
            source = expected["external"]["B"][stage]
            for key in value:
                check("same_samples." + stage + "." + key, value[key], source[key])
            same_samples[stage] = value
            lines.append(f"| {stage} | {value['n']} | {100*value['call_agreement']:.2f}% | {interval(value['kappa'], value['kappa_interval'])} |")

        lines += ["", "## Agent reruns", "",
                  "Each row uses its own coverage of the frozen agent task.", "",
                  "| Framework | System | Scored calls | Call agreement | Direction agreement | Direction AUROC |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for framework, stored in expected["reruns"].items():
            for system, source in stored["own_coverage"].items():
                if not system.startswith("R:"):
                    continue
                model, kind = system.split(":")[1:]
                filename = "agent_" + framework + "_" + model.replace("-", "_").replace(".", "_") + "_" + kind
                value = compute(filename, "agent_task158")
                source_scores(framework + "." + system, value, source)
                for key in ("direction_auroc", "direction_auroc_interval"):
                    check(framework + "." + system + "." + key, value[key], source["findings"][key])
                lines.append(f"| {framework} | {system} | {value['scored']} | {100*value['call_agreement']:.2f}% | {ratio(value['direction_agreement'])} | {value['direction_auroc']:.6f} |")
            for name in ("clockbase_agent_stored", "clockbase_atlas_verified", "constant_higher"):
                compute(name, "agent_task158")
            for model in ("gpt_6_astra", "gpt_6_sol", "gpt_6_luna", "gpt_5_5"):
                compute("language_model_" + model, "agent_task158")
            for system, source in stored["shared_agent_systems"]["metrics"].items():
                if system == "S2c":
                    name = "agent_" + framework + "_atlas_frozen"
                elif system in SYSTEM_FILES:
                    name = SYSTEM_FILES[system]
                elif system.startswith("R:"):
                    model, kind = system.split(":")[1:]
                    name = "agent_" + framework + "_" + model.replace("-", "_").replace(".", "_") + "_" + kind
                else:
                    continue
                source_scores(framework + ".shared." + system, compute(name, "agent_shared_" + framework), source)

        lines += ["", "## Expert group comparisons", "",
                  "These scores compare parsed calls with the frozen complete-group reference.", "",
                  "| Set | Stage | Orientation | Agreement | Opposite significant calls |",
                  "| --- | --- | --- | --- | --- |"]
        expert_truth = read_rows(REF / "expert_truth.csv")
        expert_results = {}
        for set_ in ("A1", "A2"):
            for stage in ("agent", "released", "candidate"):
                source_block = expected["expert_conclusions"][set_]["expert_design_call"][stage + "_call"]
                strata = ("all rows of the agent",) if stage == "agent" else ("all released rows", "labels confirmed")
                for stratum in strata:
                    ids = [r["record_id"] for r in expert_truth if r["set"] == set_ and
                           (stratum != "labels confirmed" or r["label_unconfirmed"] == "False")]
                    value = score_predictions(read_rows(REF / ("expert_" + stage + ".csv")), expert_truth, ids)
                    source = source_block[stratum]
                    check(set_ + "." + stage + "." + stratum + ".scored", value["scored"], source["units"])
                    check(set_ + "." + stage + "." + stratum + ".agreement", value["call_agreement"], (source["units"] - source["errors"]) / source["units"])
                    check(set_ + "." + stage + "." + stratum + ".opposite", value["significant_opposite"][0], source["opposite_significant"])
                    expert_results[set_ + "." + stage + "." + stratum] = value
                    lines.append(f"| {set_} | {stage} | {stratum} | {source['units']-source['errors']}/{value['scored']} | {value['significant_opposite'][0]} |")

        years = score_effects(read_rows(REF / "effect_pairs_years.csv"))
        effect_source = expected["effect_years"]["S3g"]
        for key in years:
            check("effect_years." + key, years[key], effect_source["median_absolute_difference_years" if key == "median_absolute_difference" else key])
        lines += ["", "## Effects in years", "",
                  f"The effect comparison contains {years['pairs']} estimates from {years['papers']} papers.",
                  f"Spearman correlation is {interval(years['spearman'], years['spearman_interval'])}.",
                  f"Median absolute difference is {years['median_absolute_difference']:.4f} years.", "",
                  "## Released atlas counts", "",
                  "These counts are read from the source atlas and design-check rows.", "",
                  "| Count | Value |", "| --- | --- |"]
        for key, value in notes["atlas_counts"].items():
            lines.append(f"| {key} | {value} |")
        for key, value in expected["atlas_changes"].items():
            lines.append(f"| design checks {key} | {value} |")
        lines += ["", "## Design-error source results", "",
                  "The summary table's design-error counts and intervals are retained from the",
                  "source classification analysis. This package does not repeat those classifications",
                  "or refit their design-effect-adjusted intervals.", "",
                  "| Set | Stage | Errors | Source interval |", "| --- | --- | --- | --- |"]
        for set_, stages in expected["design_error_counts"].items():
            for stage, value in stages.items():
                lines.append(f"| {set_} | {stage} | {value['k']}/{value['n']} | [{value['low']:.6f}, {value['high']:.6f}] |")
        # Check the displayed paper table independently of the JSON fixtures.
        paper_table = (REF / "paper_table.md").read_text().replace("**", "")
        table_checks = []

        def in_table(label, text):
            if text not in paper_table:
                raise ValueError(f"Paper table mismatch for {label}: {text!r}")
            table_checks.append({"metric": label, "matched_text": text})

        for set_, label in (("A1", "Mouse RNA-seq"), ("A2", "Human DNAm, all released")):
            cells = []
            for stage in ("agent", "released", "candidate"):
                stratum = "all rows of the agent" if stage == "agent" else "all released rows"
                value = expert_results[set_ + "." + stage + "." + stratum]
                n = value["scored"]
                k = round(n * value["call_agreement"])
                cells.append(f"{k} / {n} ({100*k/n:.1f}%;")
            line = next(line for line in paper_table.splitlines() if line.startswith("| " + label + " |"))
            for cell in cells:
                check("table.expert." + set_ + "." + cell, cell in line, True)
        for stage in ("released", "candidate"):
            value = expert_results["A2." + stage + ".labels confirmed"]
            n = value["scored"]
            in_table("expert.confirmed." + stage, f"{round(n*value['call_agreement'])} / {n} ({100*value['call_agreement']:.1f}%;")
        atlas_values = [compute(SYSTEM_FILES[s], "atlas_agent_shared") for s in ("S1", "S2", "S2c")]
        for key, formatter in (
            ("Three-way call,", lambda v: f"{100*v['call_agreement']:.0f}% ({v['scored']})"),
            ("Direction, published", lambda v: f"{100*v['direction_agreement'][0]/v['direction_agreement'][1]:.0f}% ({v['direction_agreement'][1]})"),
            ("Balanced accuracy of", lambda v: f"{v['balanced_accuracy']:.2f}")):
            line = next(line for line in paper_table.splitlines() if line.startswith("| " + key))
            cells = [c.strip() for c in line.split("|")[2:-1]]
            check("table." + key, [formatter(v) for v in atlas_values], cells)
        for stage, value in same_samples.items():
            in_table("same_samples." + stage + ".agreement", f"{100*value['call_agreement']:.1f}%")
            in_table("same_samples." + stage + ".kappa", f"{value['kappa']:.2f} ({value['kappa_interval'][0]:.2f}-{value['kappa_interval'][1]:.2f})")
        in_table("atlas.labels", f"{notes['atlas_counts']['labels_unconfirmed']:,} of {notes['atlas_counts']['released_rows']:,}")
        in_table("atlas.labels.dnam", f"{notes['atlas_counts']['labels_unconfirmed_human DNAm']:,} of the human DNAm rows")
        changes = expected["atlas_changes"]
        for key, denominator in (("applies", changes["rows"]), ("significant lost", changes["significant"]),
                                 ("gained", changes["rows"]-changes["significant"]), ("no call", changes["rows"])):
            in_table("atlas.changes." + key, f"{changes[key]:,} / {denominator:,} ({100*changes[key]/denominator:.1f}%)")
        for set_, stages in expected["design_error_counts"].items():
            for stage, value in stages.items():
                in_table("archived.design." + set_ + "." + stage, f"{value['k']} / {value['n']} ({100*value['k']/value['n']:.0f}%; {100*value['low']:.0f}-{100*value['high']:.0f}%)")
        lines += ["", "## Source coverage", "",
                  f"The published dataset has {len(truth)} contrasts from {len({r['paper_id'] for r in truth})}",
                  f"papers on {len({r['gse'] for r in truth})} series. The {notes['clock_output_files']} available",
                  f"clock-output tables total {notes['clock_output_source_bytes']:,} bytes and match their atlas hashes.", "",
                  "The following optional study exports are unavailable:", ""]
        lines.extend("- " + message for message in notes["missing_inputs"])
        lines += ["", "These study exports do not enter the paper-group scores. Molecular preprocessing,",
                  "source article extraction, design-error adjudication, and refitting molecular",
                  "tests are outside this reproduction. No missing measurements were substituted.", "",
                  "## Validation environment", "",
                  f"Python {platform.python_version()}; NumPy {version('numpy')}; SciPy {version('scipy')}; pytest {version('pytest')}.",
                  f"All {len(checks)} source metric comparisons passed. See `VALIDATION.md` for commands.", ""]
        write_json(REF / "reproduced_metrics.json", {"published": results, "effect_years": years, "atlas_gain": gain,
                   "expert": expert_results, "same_samples": same_samples, "source_checks": checks,
                   "paper_table_checks": table_checks})
        (ROOT / "REPORT.md").write_text("\n".join(lines).rstrip() + "\n")
        print(f"Recomputed {len(results)} published-system cohort scores, {len(expert_results)} expert scores and {len(same_samples)} same-sample scores; {len(checks)} source comparisons passed")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Cannot produce reproduction report: {error}") from error


if __name__ == "__main__":
    main()
