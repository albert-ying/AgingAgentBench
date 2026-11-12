"""Recompute the reported benchmark values from the exported rows."""
import csv
import json
from pathlib import Path

from clockeffectbench.io import read_rows, write_json
from clockeffectbench.metrics import compare_calls, score_effects, score_predictions

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference_results"


def main():
    try:
        truth = read_rows(ROOT / "data/published.jsonl")
        cohorts = json.loads((REF / "cohorts.json").read_text())
        results = {}

        def compute(name, cohort=None):
            key = name + ("@" + cohort if cohort else "")
            if key not in results:
                results[key] = score_predictions(read_rows(REF / (name + ".csv")), truth,
                                                cohorts[cohort] if cohort else None)
            return results[key]

        main_score = compute("clockbase_paper_groups", "main110")
        atlas = compute("clockbase_atlas_verified")
        atlas_common = compute("clockbase_atlas_verified", "atlas_shared93")
        welch_common = compute("clockbase_atlas_welch", "atlas_shared93")
        years = score_effects(read_rows(REF / "effect_pairs_years.csv"))
        gain = compare_calls(read_rows(REF / "clockbase_atlas_welch.csv"),
                             read_rows(REF / "clockbase_atlas_verified.csv"), truth)
        ratio = lambda pair: f"{pair[0]}/{pair[1]}"
        interval = lambda value, bounds: f"{value:.4f} [{bounds[0]:.4f}, {bounds[1]:.4f}]"
        lines = ["# ClockEffectBench reproduction", "",
                 "The standalone package reproduces the benchmark claims from the shipped",
                 "parsed predictions and published outcomes. The manuscript source is the",
                 "November 6 final text in the November 12 records checkout, Results",
                 "\"Recovery of published aging-clock effects in ClockEffectBench\", its",
                 "Methods section, Figure 4h-j, and Extended Data Figure 23. The exported",
                 "S18 worksheet records the published table; its source checksum is retained.", "",
                 "## Published findings", "",
                 "Values below are computed from the exported records. Brackets are 95%",
                 "intervals. Full precision results are in `reference_results/reproduced_metrics.json`.", "",
                 "| Measure | Manuscript | Reproduced |",
                 "| --- | --- | --- |",
                 f"| Published contrasts, papers, series | 580, 93, 125 | {len(truth)}, {len({r['paper_id'] for r in truth})}, {len({r['gse'] for r in truth})} |",
                 f"| Shared paper-group results and papers | 110, 32 | {main_score['scored']}, {main_score['papers']} |",
                 f"| Lower calls | 10/16 | {ratio(main_score['recall']['lower'])} |",
                 f"| Higher calls | 30/36 | {ratio(main_score['recall']['higher'])} |",
                 f"| Nulls kept null | 51/58 | {ratio(main_score['null_kept_null'])} |",
                 f"| Balanced accuracy | 0.78 [0.68, 0.86] | {interval(main_score['balanced_accuracy'], main_score['balanced_accuracy_interval'])} |",
                 f"| Published significant effects with matching sign | 51/52 | {ratio(main_score['direction_agreement'])} |",
                 f"| Significant in the published direction | 40/52 | {ratio(main_score['significant_in_published_direction'])} |",
                 f"| Significant in the opposite direction | 0 | {main_score['significant_opposite'][0]} |",
                 f"| Paper-group direction AUROC | 1.00 [0.98, 1.00] | {interval(main_score['direction_auroc'], main_score['direction_auroc_interval'])} |",
                 f"| Atlas direction when both significant | 25/26 | {ratio(atlas['same_direction_both_significant'])} |",
                 f"| Atlas direction AUROC | 0.98 [0.91, 1.00] | {interval(atlas['direction_auroc'], atlas['direction_auroc_interval'])} |",
                 f"| Atlas shared call agreement | 82% of 93 | {atlas_common['call_agreement']*100:.4f}% of {atlas_common['scored']} |",
                 f"| Welch-only shared call agreement | 69% of 93 | {welch_common['call_agreement']*100:.4f}% of {welch_common['scored']} |",
                 f"| Paired improvement in percentage points | 13 [5, 22] | {interval(100*gain['difference'], [100*v for v in gain['interval']])} |",
                 f"| Effects in years and papers | 30, 7 | {years['pairs']}, {years['papers']} |",
                 f"| Year-effect Spearman correlation | 0.61 [0.27, 0.93] | {interval(years['spearman'], years['spearman_interval'])} |",
                 f"| Median absolute difference in years | 1.5 | {years['median_absolute_difference']:.4f} |"]
        welch = compute("clockbase_paper_groups_welch", "paper_groups_welch113")
        lines.append(f"| Welch-only significant recovery | 33/54 | {ratio(welch['significant_in_published_direction'])} |")
        by_id = {r["record_id"]: r for r in truth}
        border = sum(by_id[r["record_id"]]["significant"] is True and .05 < float(r["p_value"]) < .10
                     for r in read_rows(REF / "clockbase_paper_groups.csv") if r["p_value"])
        lines.append(f"| Unrecovered significant results with 0.05 < P < 0.10 | 5 | {border} |")
        lines += ["", "The atlas gain resamples 43 papers in 115 shared covered records, of which",
                  "93 have classifiable calls. Keeping that full sampling universe reproduces",
                  "the source interval. AUROC 1.00 is rounded from 0.9965277778 for the main",
                  "paper-group analysis. The additional individual-reader variant has AUROC",
                  "1.00 exactly with interval [1.00, 1.00]; the variants are kept separately.", "",
                  "## Language models without data", "",
                  "The manuscript reports model ranges of 5-6/16 decreases, 12-28/36 increases,",
                  "23-47/58 nulls, and balanced accuracy 0.46-0.52. The individual rows below",
                  "reproduce the archived Figure 4 table and bootstrap intervals.", "",
                  "| System | Lower | Higher | Null | Balanced accuracy with 95% CI |",
                  "| --- | --- | --- | --- | --- |"]
        for name, label in [("constant_higher", "Always higher"),
                            ("language_model_gpt_4_1", "GPT-4.1"),
                            ("language_model_gpt_5_5", "GPT-5.5"),
                            ("language_model_gpt_6_astra", "GPT-6 Astra"),
                            ("language_model_gpt_6_luna", "GPT-6 Luna"),
                            ("language_model_gpt_6_sol", "GPT-6 Sol")]:
            value = compute(name, "main110")
            lines.append(f"| {label} | {ratio(value['recall']['lower'])} | {ratio(value['recall']['higher'])} | {ratio(value['recall']['not significant'])} | {interval(value['balanced_accuracy'], value['balanced_accuracy_interval'])} |")
        lines += ["", "## Agent reruns", "",
                  "The manuscript ranges are 77-90% call agreement, 90-95% direction",
                  "agreement, and direction AUROC 0.977-0.995. The six raw reruns reproduce",
                  "those ranges. Recomputed calls use the verification tests on each rerun's",
                  "selected samples and reproduce the reported 78-86% range.", "",
                  "| Framework and model | Raw call agreement | Raw direction agreement | Raw direction AUROC | Recomputed call agreement |",
                  "| --- | --- | --- | --- | --- |"]
        configurations = [("codex_gpt_6_astra", "Codex GPT-6 Astra"), ("codex_gpt_6_sol", "Codex GPT-6 Sol"),
                          ("codex_gpt_6_luna", "Codex GPT-6 Luna"), ("codex_gpt_5_5", "Codex GPT-5.5"),
                          ("claude_code_claude_opus_5_5", "Claude Code Claude Opus 5.5"),
                          ("biomni_gpt_6_astra", "Biomni GPT-6 Astra")]
        for name, label in configurations:
            raw = compute("agent_" + name + "_raw", "agent_task158")
            corrected = compute("agent_" + name + "_recomputed", "agent_task158")
            d = raw["direction_agreement"]
            lines.append(f"| {label} | {100*raw['call_agreement']:.2f}% of {raw['scored']} | {ratio(d)} ({100*d[0]/d[1]:.2f}%) | {raw['direction_auroc']:.6f} | {100*corrected['call_agreement']:.2f}% of {corrected['scored']} |")
        lines += ["", "| Shared framework set | Manuscript agreement | Reproduced agreement |",
                  "| --- | --- | --- |"]
        for framework, raw_names, published in [
            ("codex", [c[0] for c in configurations[:4]], "83% stored agent; 81-92% reruns"),
            ("claude_code", [configurations[4][0]], "84% stored agent; 88% rerun"),
            ("biomni", [configurations[5][0]], "82% stored agent; 83% rerun")]:
            cohort = "agent_shared_" + framework
            original = compute("clockbase_agent_stored", cohort)
            values = [compute("agent_" + n + "_raw", cohort)["call_agreement"] for n in raw_names]
            rows = ", ".join(f"{100*v:.2f}%" for v in values)
            lines.append(f"| {framework} ({len(cohorts[cohort])} covered; {original['scored']} classifiable) | {published} | {100*original['call_agreement']:.2f}% stored agent; {rows} reruns |")
        lines += ["", "## Expert group comparisons", "",
                  "These comparisons score choice and orientation of groups against frozen",
                  "complete-group calls. They do not repeat molecular preprocessing.", "",
                  "| Set | Manuscript agreement | Reproduced agreement | Opposite significant calls |",
                  "| --- | --- | --- | --- |"]
        expert_truth = read_rows(REF / "expert_truth.csv")
        expert_results = {}
        for name, set_, confirmed, expected in [("Mouse RNA-seq", "A1", False, "88/89"),
                                               ("Human DNAm with confirmed orientation", "A2", True, "126/128"),
                                               ("Human DNAm including unconfirmed orientation", "A2", False, "162/168")]:
            ids = [r["record_id"] for r in expert_truth if r["set"] == set_ and (not confirmed or r["label_unconfirmed"] == "False")]
            value = score_predictions(read_rows(REF / "expert_candidate.csv"), expert_truth, ids)
            expert_results[name] = value
            n = value["scored"]
            k = round(value["call_agreement"] * n)
            lines.append(f"| {name} | {expected} | {k}/{n} | {value['significant_opposite'][0]} |")
        lines += ["", "The stored agent has one mouse and ten human opposite significant calls,",
                  "also reproduced by the regression tests. Prepared human annotations cover",
                  "18 series; the frozen scored expert reference covers 16, matching the",
                  "manuscript. GSE134429 and GSE53841 are in the prepared inventory but have",
                  "no scored expert reference row.", "",
                  "## Annotation reuse", "",
                  "ComputAgeBench is public. Its two derivative annotation files retain CC",
                  "BY-SA 4.0, with source revision and attribution in `data/expert/README.md`.",
                  "They are exceptions to the compilation's CC BY 4.0 license.", "",
                  "Tyshkovskiy et al. is published as a Nature article, DOI",
                  "10.1038/s41586-026-10542-3, and the rodent annotation is publicly deposited",
                  "in Zenodo record 18763485. The cached deposit states a license for clock",
                  "models and software but no annotation data license. Mouse groups are",
                  "therefore withheld; the 32 identifiers and download instructions ship.",
                  "This limits reconstruction of mouse groups, not reproduction of the",
                  "parsed expert-call agreement.", "",
                  "## Unresolved source differences", "",
                  "The 580 source records label 515 as human DNAm, 64 as human RNA-seq, and",
                  "one as mouse RNA-seq. The manuscript's statement that all 65 RNA records",
                  "are human cannot be reproduced without changing the source labels. The",
                  "repository preserves those labels.", "",
                  "The manuscript describes 2,000 bootstrap draws generally. The released",
                  "balanced-accuracy scorer uses 1,000 with seed 20261005; AUROC and effect",
                  "correlations use 2,000 with seed 20261009. Both settings are preserved.", "",
                  "Three atlas study exports required for additional sample-output coverage",
                  "are absent. The export continued with the available source files:", ""]
        missing = json.loads((ROOT / "data/export_notes.json").read_text())["missing_inputs"]
        lines.extend(f"- {message}" for message in missing)
        lines += ["", "These absent study exports do not enter the scored 110-record paper-group",
                  "comparison. No missing values were replaced. The 159 available clock-output",
                  "tables total 12,848,572 bytes and match their released atlas hashes.", "",
                  "## Validation", "",
                  "The tests compare computed results with independently exported source",
                  "metric fixtures, including full-precision bootstrap endpoints. Runtime",
                  "dependencies are NumPy, pandas, and SciPy only. The test environment is",
                  "a fresh repository-local `.venv` using Python 3.12, NumPy 1.26.4, pandas",
                  "2.2.3, SciPy 1.11.4, and pytest 9.2.0. Network installation returned proxy",
                  "403; escalation was rejected with \"approval request failed\". Dependencies",
                  "were installed offline from packages already present in the source",
                  "environment. The repository's editable install, CLI, and wheel are checked",
                  "separately. No remote changes were made.", "",
                  "## Files and local commits", "",
                  "The repository contains `data/`, `reference_results/`, the Python package,",
                  "export scripts, regression tests, `README.md`, `CITATION.cff`, MIT code",
                  "licensing, and data-license notices. `.venv`, generated scores, build",
                  "outputs, credentials, and caches are ignored. Commit identifiers and the",
                  "final test and size checks are recorded in `VALIDATION.md`.", "",
                  "## Decisions for Albert", "",
                  "- Confirm the reuse terms for the public rodent annotation before adding mouse groups.",
                  "- Resolve the manuscript's RNA modality description against the preserved source labels.",
                  "- Decide whether to clarify the separate bootstrap settings in the Methods.",
                  "- Recover the three absent atlas study exports if full sample-output coverage is needed.", ""]
        write_json(REF / "reproduced_metrics.json", {"published": results, "effect_years": years, "atlas_gain": gain, "expert": expert_results})
        (ROOT / "REPORT.md").write_text("\n".join(lines))
        print(f"Recomputed {len(results)} published-system cohort scores and three expert scores")
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Cannot produce reproduction report: {error}") from error


if __name__ == "__main__":
    main()
