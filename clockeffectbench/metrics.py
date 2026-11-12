"""Released metric definitions and bootstrap settings.

Balanced accuracy uses summarize_2026_10_05 (1,000 draws, seed 20261005).
AUROC and effect intervals use design_eval (2,000 draws, seed 20261009).
"""
from collections import defaultdict
import math

import numpy as np
from scipy import stats

CLASSES = ("lower", "higher", "not significant")
ALIASES = {"none": "not significant", "not_significant": "not significant"}


def number(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("A numeric field cannot be a boolean")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Numeric fields must be finite")
    return result


def normalize_call(value):
    value = ALIASES.get(value, value)
    if value not in CLASSES:
        raise ValueError(f"Invalid call {value!r}; use higher, lower, or not significant")
    return value


def truth_call(record):
    explicit = record.get("published_call", record.get("truth_call"))
    if explicit:
        return normalize_call(explicit)
    sig = record.get("significant")
    if sig is False:
        return "not significant"
    if sig is True and record.get("direction") in ("higher", "lower"):
        return record["direction"]
    return None


def paper_key(record):
    if record.get("paper_id"):
        return str(record["paper_id"])
    source = record.get("source") or {}
    return str(next((source[k] for k in ("doi", "pmid", "pmcid", "citation", "url") if source.get(k)),
                    record.get("record_id", record.get("id"))))


def signed_z(direction, p_value):
    if direction not in ("higher", "lower", "none") or p_value is None:
        return None
    if direction == "none":
        return 0.0
    return float(np.copysign(stats.norm.isf(max(p_value, 1e-300) / 2),
                            1 if direction == "higher" else -1))


def auroc(positive, negative):
    if not positive or not negative:
        return None
    return float(stats.mannwhitneyu(positive, negative, alternative="two-sided", method="asymptotic").statistic
                 / (len(positive) * len(negative)))


def bootstrap(items, statistic, replicates, seed):
    groups = defaultdict(list)
    for item in items:
        groups[item["paper_id"]].append(item)
    keys = sorted(groups)
    values = []
    rng = np.random.default_rng(seed)
    if len(keys) >= 2:
        for _ in range(replicates):
            sample = [r for i in rng.integers(0, len(keys), len(keys)) for r in groups[keys[i]]]
            value = statistic(sample)
            if value is not None and math.isfinite(value):
                values.append(value)
    return ([float(np.quantile(values, .025)), float(np.quantile(values, .975))] if values else None)


def balanced(items):
    # Resamples average over the reference classes present, as in the source.
    items = [r for r in items if r.get("truth") in CLASSES and r.get("call") in CLASSES]
    classes = sorted({r["truth"] for r in items})
    return float(np.mean([np.mean([r["call"] == c for r in items if r["truth"] == c])
                          for c in classes])) if classes else None


def finding_auc(items):
    return auroc([r["z"] for r in items if r["truth"] == "higher"],
                 [r["z"] for r in items if r["truth"] == "lower"])


def effect_pair(record, prediction):
    effect = record.get("effect") or {}
    if not isinstance(effect, dict):
        return None
    published = number(effect.get("value"))
    if published is None or record.get("modality") != "human DNAm":
        return None
    if not str(effect.get("unit", "")).lower().startswith("year"):
        return None
    if "uncertain" in str(effect.get("type", "")).lower():
        return None
    if record.get("direction") in ("higher", "lower") and published != 0 and (published > 0) != (record["direction"] == "higher"):
        return None
    predicted = number(prediction.get("effect"))
    if predicted is None or prediction.get("effect_unit", "").lower() not in ("year", "years"):
        return None
    return published, predicted


def effect_spearman(items):
    if len(items) < 3:
        return None
    x, y = [r["published"] for r in items], [r["predicted"] for r in items]
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return float(stats.spearmanr(x, y).statistic)


def score_predictions(predictions, ground_truth, record_ids=None):
    """Score calls and optional P values, signed directions and effects.

    Missing predictions reduce coverage. Unknown and duplicate identifiers and
    contradictory calls are errors. Effects require an explicit unit.
    """
    truth = {r.get("record_id", r.get("id")): r for r in ground_truth}
    if len(truth) != len(ground_truth) or None in truth:
        raise ValueError("Ground truth identifiers must be present and unique")
    selected = set(record_ids) if record_ids is not None else set(truth)
    if not selected <= truth.keys():
        raise ValueError("Cohort contains unknown ground truth identifiers")
    items, findings, effects, directions, seen = [], [], [], [], set()
    for prediction in predictions:
        key = prediction.get("record_id", prediction.get("id"))
        if key not in truth:
            raise ValueError(f"Unknown record_id: {key!r}")
        if key in seen:
            raise ValueError(f"Duplicate record_id: {key}")
        seen.add(key)
        call = normalize_call(prediction["call"]) if prediction.get("call") else None
        p = number(prediction.get("p_value"))
        if p is not None and not 0 <= p <= 1:
            raise ValueError(f"P value outside [0, 1] for {key}")
        effect = number(prediction.get("effect"))
        direction = prediction.get("direction") or ("higher" if effect is not None and effect > 0 else
                     "lower" if effect is not None and effect < 0 else "none" if effect == 0 else
                     call if call in ("higher", "lower") else None)
        if direction not in (None, "higher", "lower", "none"):
            raise ValueError(f"Invalid direction for {key}")
        if call is None and direction is None:
            raise ValueError(f"A call or direction is required for {key}")
        if call in ("higher", "lower") and direction != call:
            raise ValueError(f"Call contradicts direction for {key}")
        if effect is not None and effect != 0 and direction in ("higher", "lower") and (effect > 0) != (direction == "higher"):
            raise ValueError(f"Effect contradicts direction for {key}")
        if key not in selected:
            continue
        record = truth[key]
        cluster = paper_key(record)
        pair = effect_pair(record, prediction)
        if pair is not None:
            effects.append({"paper_id": cluster, "published": pair[0], "predicted": pair[1]})
        actual = truth_call(record)
        if actual is None:
            continue
        item = {"paper_id": cluster, "record_id": key, "truth": actual, "call": call, "direction": direction}
        if actual in ("higher", "lower") and direction is not None:
            directions.append(item)
        if call is not None:
            items.append(item)
        z = signed_z(direction, p)
        if z is not None and call is not None:
            findings.append(dict(item, z=z))
    significant = [i for i in items if i["truth"] != "not significant"]
    directed = directions
    nulls = [i for i in items if i["truth"] == "not significant"]
    both = [i for i in significant if i["call"] != "not significant"]
    matrix = [[sum(i["call"] == predicted and i["truth"] == actual for i in items)
               for actual in CLASSES] for predicted in CLASSES]
    recalls = {c: [sum(i["truth"] == c and i["call"] == c for i in items),
                   sum(i["truth"] == c for i in items)] for c in CLASSES}
    calls_by_id = {r["record_id"]: r["call"] for r in items}
    # The source resamples the entire requested cohort, including papers with
    # unanswered or unclassifiable rows. Such rows make no contribution to
    # point estimates but retain the original bootstrap sampling universe.
    bootstrap_cohort = [{"paper_id": paper_key(r), "truth": truth_call(r),
                         "call": calls_by_id.get(key)} for key, r in truth.items() if key in selected]
    return {
        "records_in_cohort": len(selected), "submitted": len(seen & selected), "scored": len(items),
        "papers": len({i["paper_id"] for i in items}),
        "call_agreement": (sum(i["call"] == i["truth"] for i in items) / len(items) if items else None),
        "recall": recalls,
        "confusion_matrix": {"rows": list(CLASSES), "columns": list(CLASSES), "values": matrix},
        "balanced_accuracy": balanced(items),
        "balanced_accuracy_interval": bootstrap(bootstrap_cohort, balanced, 1000, 20261005),
        "published_significant": len(significant),
        "direction_agreement": [sum(i["direction"] == i["truth"] for i in directed), len(directed)],
        "significant_in_published_direction": [sum(i["call"] == i["truth"] for i in significant), len(significant)],
        "significant_opposite": [sum(i["call"] != i["truth"] for i in both), len(significant)],
        "same_direction_both_significant": [sum(i["call"] == i["truth"] for i in both), len(both)],
        "null_kept_null": [sum(i["call"] == "not significant" for i in nulls), len(nulls)],
        "direction_auroc": finding_auc(findings),
        "direction_auroc_interval": bootstrap(findings, finding_auc, 2000, 20261009),
        "auroc_significant_records": sum(i["truth"] != "not significant" for i in findings),
        "effect_years": {
            "pairs": len(effects), "papers": len({i["paper_id"] for i in effects}),
            "spearman": effect_spearman(effects),
            "spearman_interval": bootstrap(effects, effect_spearman, 2000, 20261009),
            "median_absolute_difference": float(np.median([abs(i["published"]-i["predicted"]) for i in effects])) if effects else None,
        },
        "bootstrap": {"unit": "paper", "level": .95,
                      "balanced_accuracy": {"replicates": 1000, "seed": 20261005},
                      "auroc_and_effect": {"replicates": 2000, "seed": 20261009}},
    }


def score_effects(pairs):
    """Score exported year effects with the original paper bootstrap."""
    items, seen = [], set()
    for pair in pairs:
        key = pair["record_id"]
        if key in seen:
            raise ValueError(f"Duplicate effect record_id: {key}")
        seen.add(key)
        if pair.get("unit", pair.get("effect_unit")) not in ("years", "year"):
            raise ValueError(f"Effect unit must be years for {key}")
        published, predicted = number(pair.get("published_effect")), number(pair.get("effect"))
        if published is None or predicted is None:
            continue
        items.append({"paper_id": pair["paper_id"], "published": published, "predicted": predicted})
    return {"pairs": len(items), "papers": len({r["paper_id"] for r in items}),
            "spearman": effect_spearman(items),
            "spearman_interval": bootstrap(items, effect_spearman, 2000, 20261009),
            "median_absolute_difference": float(np.median([abs(r["published"]-r["predicted"]) for r in items])) if items else None}


def compare_calls(before, after, ground_truth):
    """Paired change in call agreement using the source's shared universe."""
    left = {r["record_id"]: r for r in before}
    right = {r["record_id"]: r for r in after}
    if len(left) != len(before) or len(right) != len(after):
        raise ValueError("Comparison predictions have duplicate identifiers")
    items = [{"paper_id": paper_key(r), "truth": truth_call(r),
              "before": left[r["record_id"]].get("call"),
              "after": right[r["record_id"]].get("call")}
             for r in ground_truth if r["record_id"] in left and r["record_id"] in right]

    def gain(rows):
        usable = [r for r in rows if r["truth"] and r["before"] and r["after"]]
        if not usable:
            return None
        return (float(np.mean([r["truth"] == r["after"] for r in usable]))
                - float(np.mean([r["truth"] == r["before"] for r in usable])))

    return {"difference": gain(items), "interval": bootstrap(items, gain, 2000, 20261009),
            "common_records": len(items), "papers": len({r["paper_id"] for r in items}),
            "scored": sum(bool(r["truth"] and r["before"] and r["after"]) for r in items)}
