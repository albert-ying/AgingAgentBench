"""Export parsed benchmark data from a local ClockBase records checkout.

This command reads existing results only. It performs no model or API calls.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read {path.name}: {error}") from error


def read_jsonl(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read {path.name}: {error}") from error


def write_json(path, value):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    except OSError as error:
        raise ValueError(f"Cannot write {path.name}: {error}") from error


def write_jsonl(path, values):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in values))
    except OSError as error:
        raise ValueError(f"Cannot write {path.name}: {error}") from error


def write_csv(path, records):
    try:
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            for record in records:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list))
                                 else v for k, v in record.items()})
    except OSError as error:
        raise ValueError(f"Cannot write {path.name}: {error}") from error


def paper_key(record):
    source = record.get("source") or {}
    return next((str(source[k]) for k in ("doi", "pmid", "pmcid", "citation", "url") if source.get(k)), record["id"])


def holds(rule, sample):
    return any(all(str(sample.get(p["source"], {}).get(p["field"])) in set(map(str, p["values"]))
                   for p in group) for group in rule or [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Local revision folder holding data/ and aging-ai-nature-appeal/.")
    parser.add_argument("--out", type=Path, default=Path("data"))
    args = parser.parse_args()
    source = args.source_root.resolve()
    bench = source / "data/clockbase-benchmark-2026-10-05"
    verifier = source / "data/clockbase-verifier-v3-2026-09-27"
    bundle = source / "data/bundle/clockbase_data"
    atlas = verifier / "final-2026-11-12/public-export"
    results = source / "aging-ai-nature-appeal/benchmark/published_clock_2026_10_05/groupbench/results_2026_11_12"
    receipts, missing = {}, []

    def receipt(path):
        relative = str(path.relative_to(source))
        if not path.exists():
            message = f"Cannot proceed - required data file not found: {relative}"
            if message not in missing:
                missing.append(message)
            return None
        if relative not in receipts:
            receipts[relative] = {"path": relative, "bytes": path.stat().st_size,
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        return receipts[relative]

    gt_path = bench / "ground_truth_t1_v2_final_2026-10-05.jsonl"
    if not receipt(gt_path):
        write_json(args.out / "export_notes.json", {"missing_inputs": missing})
        return
    ground_truth = read_jsonl(gt_path)
    engine = {}
    for name in ("t1-openai-002-s4", "t1new-openai-001-s4"):
        path = bench / "runs" / name / "records.jsonl"
        if receipt(path):
            engine.update({r["id"]: r for r in read_jsonl(path)})
    released_path = results / "published_released_test.csv"
    released = {}
    if receipt(released_path):
        with released_path.open() as handle:
            released = {r["id"]: r for r in csv.DictReader(handle)}

    # Bibliographic metadata are read from cached Europe PMC search results.
    bibliography = {}
    for path in sorted((bench / "retrieval/cache").glob("*.json")):
        metadata = read_json(path)
        if "/search?" not in metadata.get("url", ""):
            continue
        body = path.with_suffix(".body")
        if not body.exists():
            continue
        try:
            search = json.loads(body.read_text())
        except (OSError, ValueError):
            continue
        for paper in search.get("resultList", {}).get("result", []):
            if paper.get("authorString"):
                bibliography[paper.get("id")] = (paper, body)
    pheno_path = bench / "curated/downloads/phenoage-search.json"
    if receipt(pheno_path):
        for paper in read_json(pheno_path).get("resultList", {}).get("result", []):
            bibliography[paper.get("id")] = (paper, pheno_path)

    exported = []
    for record in ground_truth:
        original = record.get("source") or {}
        paper, bib_path = bibliography.get(original.get("pmid") or original.get("id"), ({}, None))
        if bib_path:
            receipt(bib_path)
        quote = original.get("quote") or ""
        # Keep one contiguous prefix of the first source passage, never an added paraphrase.
        quote = quote.split(" ... ")[0]
        words = list(re.finditer(r"\S+", quote))
        short_quote = quote[:words[min(25, len(words)) - 1].end()] if words else ""
        source_fields = {k: original.get(k) for k in ("paper_id", "doi", "pmid", "pmcid", "citation", "year", "location")}
        source_fields.update(first_author=(paper.get("authorString") or "").split(",")[0] or None,
                             quote=short_quote,
                             url=original.get("url") or (f"https://doi.org/{original['doi']}" if original.get("doi")
                                                         else f"https://pubmed.ncbi.nlm.nih.gov/{original['pmid']}/" if original.get("pmid") else None))
        if not source_fields["year"]:
            source_fields["year"] = paper.get("pubYear")
        if source_fields["citation"] == "phenoage" and paper.get("title"):
            source_fields["citation"] = paper["title"]
        evaluated = engine.get(record["id"], {})
        groups = evaluated.get("groups") or {}
        eligibility = {}
        for system, prediction in (evaluated.get("systems") or {}).items():
            eligibility[system] = {"testable": bool(prediction.get("covered")),
                                   "status": prediction.get("status")}
        release = released.get(record["id"], {})
        eligibility["clockbase_paper_groups"] = {"testable": bool(release.get("S3c_call")),
                                                  "status": release.get("S3c_method") or "NOT_SCORED"}
        published_call = (record["direction"] if record.get("significant") is True and record.get("direction") in ("higher", "lower")
                          else "not significant" if record.get("significant") is False or record.get("direction") == "none" else None)
        keep = ("tier", "gse", "modality", "tissue", "clock_reported", "clock_clockbase", "measure",
                "case_label", "control_label", "case_definition", "control_definition", "n_case", "n_control",
                "direction", "significant", "threshold", "p_value", "test", "covariates", "effect")
        item = {"record_id": record["id"], "id": record["id"], "paper_id": paper_key(record),
                **{k: record.get(k) for k in keep}, "published_call": published_call, "source": source_fields,
                "case_gsms": groups.get("case_gsms") or [], "control_gsms": groups.get("control_gsms") or [],
                "groups_status": groups.get("status") or "NOT_ASSIGNED", "eligibility": eligibility}
        exported.append(item)
    write_jsonl(args.out / "published.jsonl", exported)
    write_csv(args.out / "published.csv", exported)

    units_path = bench / "groupbench/prepared-v2/units.jsonl"
    declared_path = bench / "groupbench/frozen-v2/declared.json"
    units = read_jsonl(units_path) if receipt(units_path) else []
    declared = read_json(declared_path) if receipt(declared_path) else {}
    label_path = bench / "groupbench/a2/labels.csv"
    meta_path = bench / "groupbench/a2/computage_bench_meta_3cf5268.tsv"
    human_groups, human_samples, human_series, mouse_series = [], [], set(), set()
    label_rows, cells = [], {}
    if receipt(label_path):
        with label_path.open() as handle:
            label_rows = list(csv.DictReader(handle))
    if receipt(meta_path):
        with meta_path.open() as handle:
            cells = {(r["DatasetID"], r["SampleID"]): r["CellType"] for r in csv.DictReader(handle, delimiter="\t")}
    series_cache = {}
    for unit in units:
        gse = unit["gse"]
        if unit["set"] == "A1":
            mouse_series.add(gse)
            continue
        human_series.add(gse)
        if gse not in series_cache:
            path = bundle / "GEO_data/GEO_hs_dnam/processed_metadata_preharmonize" / f"{gse}.csv"
            if not receipt(path):
                series_cache[gse] = {}
                continue
            with path.open() as handle:
                series = {r["GSM"]: {"geo": {k: v for k, v in r.items() if k != "GSM"}, "expert": {}}
                          for r in csv.DictReader(handle)}
            for label in label_rows:
                if label["gsm"] not in series:
                    continue
                value = {k: label[k] for k in ("condition", "class", "age", "tissue", "sex")}
                value["cell_type"] = cells.get((label["dataset"], label["gsm"]), "")
                previous = series[label["gsm"]]["expert"]
                if previous:
                    value = {k: v if previous.get(k) == v else None for k, v in value.items()}
                series[label["gsm"]]["expert"] = value
            series_cache[gse] = series
            human_samples.extend({"gse": gse, "gsm": gsm, **sample} for gsm, sample in sorted(series.items()))
        for index, variant in enumerate(unit["variants"]):
            contrast = declared.get(f"{unit['unit_id']}#{index}")
            if not contrast or contrast.get("status") == "ambiguous":
                continue
            series = series_cache[gse]
            human_groups.append({"unit_id": unit["unit_id"], "variant": index, "gse": gse,
                "case_label": contrast.get("case_level"), "control_label": contrast.get("reference_level"),
                "case_rule": contrast["case_rule"], "control_rule": contrast["reference_rule"],
                "case_gsms": [g for g, sample in series.items() if holds(contrast["case_rule"], sample)],
                "control_gsms": [g for g, sample in series.items() if holds(contrast["reference_rule"], sample)],
                "comparison_id": variant["comparison_id"], "source": "ComputAgeBench",
                "source_revision": "3cf52681537b303a5b7e21df03a3ae0a94ed497e", "license": "CC-BY-SA-4.0"})
    write_jsonl(args.out / "expert/human_dnam_groups.jsonl", human_groups)
    write_jsonl(args.out / "expert/human_dnam_samples.jsonl", human_samples)
    expert_manifest = {"mouse_rna_series": sorted(mouse_series), "human_dnam_series": sorted(human_series),
        "mouse_annotation": {"publication_doi": "10.1038/s41586-026-10542-3", "publication_status": "published",
            "annotation_url": "https://zenodo.org/records/18763485/files/Data_annotation_absolute_rodents.xlsx",
            "license_status": "Cached public deposit does not state a data license; group definitions withheld pending clarification."},
        "human_annotation": {"publication_doi": "10.1101/2024.06.06.597715", "dataset_doi": "10.57967/hf/4347",
            "url": "https://huggingface.co/datasets/computage/computage_bench/tree/3cf52681537b303a5b7e21df03a3ae0a94ed497e",
            "revision": "3cf52681537b303a5b7e21df03a3ae0a94ed497e", "license": "CC-BY-SA-4.0",
            "attribution": "Kriukov D, Efimov E, Kuzmina EA, Khrameeva EE, Dylov DV. ComputAgeBench: Epigenetic Aging Clocks Benchmark."}}
    write_json(args.out / "expert/sources.json", expert_manifest)
    receipt(bench / "groupbench/a1/source/zenodo_18763485.json")
    receipt(bench / "groupbench/a2/SOURCE.json")
    receipt(bench / "groupbench/a2/computage_README_3cf5268.md")

    # Copy numerical clock tables only, never study exports containing agent traces.
    pairs = {(r["modality"], r["gse"]) for r in ground_truth}
    pairs |= {({"A1": "mouse RNA-seq", "A2": "human DNAm"}[r["set"]], r["gse"]) for r in units}
    clock_sources = {}
    modality_map = {"human DNAm": "dnam", "human RNA-seq": "hs_rna", "mouse RNA-seq": "mm_rna"}
    root_map = {"verifier": verifier, "stream_empty": bundle / "dnam-stream-repair-empty",
                "stream_detached": bundle / "dnam-stream-repair-detached"}
    for modality, gse in sorted(pairs):
        study_path = atlas / "studies" / modality_map[modality] / f"{gse}.json"
        if not receipt(study_path):
            continue
        study = read_json(study_path)
        for row in study.get("rows", []):
            pred = row.get("predictions") or {}
            if not pred.get("path"):
                continue
            namespace, relative = pred["path"].split(":", 1)
            path = root_map[namespace] / relative
            key = str(path.relative_to(source))
            entry = clock_sources.setdefault(key, {"path": path, "modality": modality, "gse": gse, "clocks": set(),
                                                   "expected_sha256": pred.get("sha256")})
            entry["clocks"].add(row["clock"])
    total_bytes = sum(e["path"].stat().st_size for e in clock_sources.values() if e["path"].exists())
    output_manifest = []
    if total_bytes < 50_000_000:
        for key, entry in sorted(clock_sources.items()):
            info = receipt(entry["path"])
            if info is None:
                continue
            name = f"{entry['gse']}_{hashlib.sha256(key.encode()).hexdigest()[:8]}.csv"
            target = args.out / "clockbase_outputs" / modality_map[entry["modality"]] / name
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(["/bin/cp", "-f", str(entry["path"]), str(target)], check=True)
            except (OSError, subprocess.CalledProcessError) as error:
                raise ValueError(f"Cannot copy clock outputs for {entry['gse']}: {error}") from error
            output_manifest.append({"gse": entry["gse"], "modality": entry["modality"],
                "file": str(target.relative_to(args.out / "clockbase_outputs")), "clocks": sorted(entry["clocks"]),
                "bytes": info["bytes"], "sha256": info["sha256"], "source": key,
                "atlas_expected_sha256": entry["expected_sha256"], "hash_matches_atlas": info["sha256"] == entry["expected_sha256"]})
    write_json(args.out / "clockbase_outputs/manifest.json", output_manifest)
    notes = {"export_date": "2026-11-12", "published_records": len(exported),
        "papers": len({r["paper_id"] for r in exported}), "series": len({r["gse"] for r in exported}),
        "modality_counts": dict(Counter(r["modality"] for r in exported)),
        "first_author_missing": [r["id"] for r in exported if not r["source"]["first_author"]],
        "quote_policy": "A contiguous prefix of at most 25 whitespace-delimited words from the first extracted evidence passage; statistics retained from the full source extraction.",
        "mouse_annotation_status": expert_manifest["mouse_annotation"]["license_status"],
        "expert_series_counts": {"mouse_rna": len(mouse_series), "human_dnam": len(human_series)},
        "clock_output_source_bytes": total_bytes, "clock_output_files": len(output_manifest),
        "clock_output_hash_mismatches": [r["file"] for r in output_manifest if not r["hash_matches_atlas"]],
        "missing_inputs": missing, "inputs": list(receipts.values())}
    write_json(args.out / "export_notes.json", notes)
    print(json.dumps({k: v for k, v in notes.items() if k != "inputs"}, indent=2))


if __name__ == "__main__":
    main()
