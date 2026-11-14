"""Validated CSV and JSONL input and portable bundled resource lookup."""
import csv
import json
from importlib.resources import files
from pathlib import Path


def resource(folder, name):
    checkout = Path(__file__).resolve().parents[1] / folder / name
    if checkout.is_file():
        return checkout
    return Path(str(files(f"agingagentbench.{folder}").joinpath(name)))


def read_rows(path):
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            if path.suffix.lower() == ".csv":
                rows = list(csv.DictReader(handle))
                # The published CSV stores nested fields as JSON. Prediction
                # effect columns remain numeric scalars.
                for row in rows:
                    for key in ("source", "effect", "eligibility", "case_gsms", "control_gsms", "covariates"):
                        value = row.get(key)
                        if value and value.lstrip().startswith(("{", "[")):
                            row[key] = json.loads(value)
                    if "significant" in row:
                        row["significant"] = {"True": True, "False": False, "": None}.get(
                            row["significant"], row["significant"])
                return rows
            if path.suffix.lower() == ".jsonl":
                return [json.loads(line) for line in handle if line.strip()]
        raise ValueError("Input must be a CSV or JSONL file")
    except FileNotFoundError as error:
        raise ValueError(f"Cannot proceed - required data file not found: {path}") from error
    except (OSError, csv.Error, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error


def write_json(path, value):
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot write score file {path}: {error}") from error
