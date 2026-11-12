"""Extract frozen input prompts only, without responses or API settings."""
import argparse
import hashlib
import json
from pathlib import Path

from clockeffectbench.prompts import redact_emails


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/prompts.jsonl"))
    args = parser.parse_args()
    root = args.source_root / "data/clockbase-benchmark-2026-10-05"
    try:
        final = {r["id"] for r in map(json.loads, (root / "ground_truth_t1_v2_final_2026-10-05.jsonl").read_text().splitlines())}
        unique = {}
        provenance = []
        for name in ("s4-openai-001-gpt-4.1", "s4-openai-002-gpt-4.1"):
            folder = root / "runs" / name
            predictions = [json.loads(line) for line in (folder / "predictions.jsonl").read_text().splitlines()]
            identifiers = {}
            for prediction in predictions:
                if prediction["record_id"] in final:
                    identifiers.setdefault(prediction["request_hash"], set()).add(prediction["record_id"])
            for line in (folder / "requests.jsonl").read_text().splitlines():
                request = json.loads(line)
                keys = identifiers.get(request["request_hash"], set())
                if not keys:
                    continue
                prompt = next(m["content"] for m in request["request"]["messages"] if m["role"] == "user")
                cleaned = redact_emails(prompt)
                flags = list(request.get("prompt_flags", []))
                if cleaned != prompt:
                    flags.append("geo_email_redacted")
                for key in sorted(keys):
                    unique[key] = {"record_id": key, "prompt": cleaned, "flags": flags}
            provenance.append({"source": f"records deposit/benchmark/runs/{name}/requests.jsonl",
                               "sha256": hashlib.sha256((folder / "requests.jsonl").read_bytes()).hexdigest(),
                               "mtime_ns": (folder / "requests.jsonl").stat().st_mtime_ns})
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in unique.values()))
        manifest = {"records": len(unique), "inputs": provenance,
                    "selection": "Round 002 takes precedence over round 001 for a repeated record.",
                    "content": "User input prompts and blinding flags; third-party email addresses replaced by [email removed]."}
        args.out.with_name("prompts_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Exported {len(unique)} frozen input prompts")
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot proceed - required data file not found: {error.filename}") from error
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Cannot export input prompts: {error}") from error


if __name__ == "__main__":
    main()
