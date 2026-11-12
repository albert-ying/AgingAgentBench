"""Read the published S18 worksheet without changing its source workbook."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("reference_results/supplementary_table_s18.csv"))
    args = parser.parse_args()
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    try:
        with ZipFile(args.workbook) as archive:
            strings = (["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns)]
                       if "xl/sharedStrings.xml" in archive.namelist() else [])
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
            sheet = next(s for s in workbook.findall("s:sheets/s:sheet", ns) if s.attrib["name"] == "S18")
            target = rels[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            root = ET.fromstring(archive.read("xl/" + target.lstrip("/").removeprefix("xl/")))
            rows, title = [], ""
            for row in root.findall("s:sheetData/s:row", ns):
                values = [""] * 11
                for cell in row.findall("s:c", ns):
                    ref = cell.attrib["r"]
                    column = "".join(c for c in ref if c.isalpha())
                    if len(column) != 1 or column > "K":
                        continue
                    v = cell.find("s:v", ns)
                    value = v.text if v is not None else ""
                    if cell.attrib.get("t") == "s":
                        value = strings[int(value)]
                    elif cell.attrib.get("t") == "inlineStr":
                        value = "".join(cell.find("s:is", ns).itertext())
                    values[ord(column) - ord("A")] = value
                if row.attrib["r"] == "1":
                    title = values[0]
                elif any(values):
                    rows.append(values)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="") as handle:
            csv.writer(handle).writerows(rows)
        manifest = {"source": args.workbook.name, "sheet": "S18", "records": len(rows) - 1,
                    "sha256": hashlib.sha256(args.workbook.read_bytes()).hexdigest(),
                    "mtime_ns": args.workbook.stat().st_mtime_ns, "caption": title,
                    "transformation": "Cell values A:K exported without workbook formatting; no recalculation."}
        args.out.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Exported {len(rows) - 1} S18 rows")
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot proceed - required data file not found: {error.filename}") from error
    except (OSError, KeyError, ValueError, StopIteration) as error:
        raise SystemExit(f"Cannot extract S18: {error}") from error


if __name__ == "__main__":
    main()
