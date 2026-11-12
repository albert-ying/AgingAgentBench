"""Command line scoring and frozen prompt access without network requests."""
import argparse
import json
from pathlib import Path
import sys

from .io import read_rows, resource, write_json
from .metrics import effect_pair, paper_key, score_effects, score_predictions
from .prompts import build_prompt


def cohort_ids(name):
    if name == "all":
        return None
    cohorts = json.loads(resource("reference_results", "cohorts.json").read_text())
    if name not in cohorts:
        raise ValueError(f"Unknown cohort {name!r}; choose all or " + ", ".join(cohorts))
    return cohorts[name]


def run_score(args):
    truth = read_rows(args.ground_truth or resource("reference_results" if args.expert else "data",
                                                 "expert_truth.csv" if args.expert else "published.jsonl"))
    ids = cohort_ids(args.cohort)
    if args.expert:
        if args.cohort != "all":
            raise ValueError("Expert scores use --expert-set rather than published cohorts")
        subset = truth
        if args.expert_set != "all":
            wanted = "A1" if args.expert_set.startswith("mouse") else "A2"
            subset = [r for r in subset if r["set"] == wanted]
        if args.expert_set.endswith("-confirmed"):
            subset = [r for r in subset if r["label_unconfirmed"] == "False"]
        ids = [r["record_id"] for r in subset]
    predictions = read_rows(args.predictions)
    result = score_predictions(predictions, truth, ids)
    if args.effects:
        if args.expert:
            raise ValueError("Published year effects are unavailable for the expert task")
        indexed = {r["record_id"]: r for r in truth}
        selection = read_rows(args.effects)
        effect_ids = [r.get("record_id") for r in selection]
        if len(effect_ids) != len(set(effect_ids)):
            raise ValueError("Duplicate effect record_id in selection file")
        for key in effect_ids:
            if key not in indexed:
                raise ValueError(f"Unknown effect record_id: {key}")
        chosen = set(effect_ids)
        pairs = []
        for prediction in predictions:
            key = prediction.get("record_id", prediction.get("id"))
            if key in chosen:
                pair = effect_pair(indexed[key], prediction)
                if pair is not None:
                    pairs.append({"record_id": key, "paper_id": paper_key(indexed[key]),
                                  "published_effect": pair[0], "effect": pair[1], "unit": "years"})
        result["effect_years"] = score_effects(pairs)
        result["effect_cohort"] = {"selected": len(chosen), "source": "predictions",
                                   "restriction": "Independent of the call cohort"}
    output = args.output or Path("scores") / (args.predictions.stem + "_" + (args.expert_set if args.expert else args.cohort) + ".json")
    write_json(output, result)
    print(json.dumps(result, indent=2, allow_nan=False))
    print(f"Wrote {output}", file=sys.stderr)


def run_prompt(args):
    if not args.record_id:
        args.record_id = json.loads(resource("reference_results", "cohorts.json").read_text())["main110"][0]
    if args.study:
        truth = {r["record_id"]: r for r in read_rows(resource("data", "published.jsonl"))}
        if args.record_id not in truth:
            raise ValueError(f"Unknown record_id: {args.record_id}")
        study = json.loads(args.study.read_text())
        print(build_prompt(truth[args.record_id], study)["prompt"])
        return
    prompts = {r["record_id"]: r for r in read_rows(resource("data", "prompts.jsonl"))}
    if args.record_id not in prompts:
        raise ValueError(f"No frozen prompt for {args.record_id}; neutral prompts are shipped for 324 records only. The builder supports the 16 clocks in CLOCKS and four measures and can reject unsupported or revealing inputs.")
    print(prompts[args.record_id]["prompt"])


def main(argv=None):
    parser = argparse.ArgumentParser(prog="clockeffectbench", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    score = commands.add_parser("score", help="Print and write metrics for a predictions file")
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--cohort", default="all", help="all, main110, atlas_shared93, or an agent cohort")
    score.add_argument("--ground-truth", type=Path, help="Optional ground truth CSV or JSONL")
    score.add_argument("--output", type=Path, help="Defaults to scores/PREDICTIONS_COHORT.json")
    score.add_argument("--effects", type=Path, help="Select year-effect record_ids; estimates and units come from --predictions")
    score.add_argument("--expert", action="store_true", help="Use the frozen expert-group call reference")
    score.add_argument("--expert-set", choices=("all", "mouse", "mouse-confirmed", "human", "human-confirmed"), default="all")
    score.set_defaults(run=run_score)
    prompt = commands.add_parser("prompt", help="Print a neutral language-model input without API calls")
    prompt.add_argument("record_id", nargs="?", help="Defaults to the first main110 record")
    prompt.add_argument("--study", type=Path, help="Build a new prompt from local GEO description JSON")
    prompt.set_defaults(run=run_prompt)
    args = parser.parse_args(argv)
    try:
        args.run(args)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"clockeffectbench: {error}\n")


if __name__ == "__main__":
    main()
