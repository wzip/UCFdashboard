import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from PyPDF2 import PdfReader

COUNTIES = [
    "Atlantic",
    "Bergen",
    "Burlington",
    "Camden",
    "Cape May",
    "Cumberland",
    "Essex",
    "Gloucester",
    "Hudson",
    "Hunterdon",
    "Mercer",
    "Middlesex",
    "Monmouth",
    "Morris",
    "Ocean",
    "Passaic",
    "Salem",
    "Somerset",
    "Sussex",
    "Union",
    "Warren",
]


def extract_header(text: str) -> Dict[str, Optional[str]]:
    match = re.search(r"Municipality:\s*County:\s*(.+?)A C C R E D I T A T I O N", text)
    municipality = None
    county = None
    if match:
        segment = re.sub(r"\s+", " ", match.group(1)).strip()
        for candidate in COUNTIES:
            if segment.lower().endswith(candidate.lower()):
                county = candidate
                municipality = segment[: -len(candidate)].strip()
                break
    return {"municipality": municipality, "county": county}


def extract_updated(text: str) -> Optional[str]:
    match = re.search(r"Updated:\s*([0-9/]+)", text)
    return match.group(1) if match else None


def extract_plan_year(text: str) -> Optional[int]:
    match = re.search(r"(20\d{2})\s+Most Recent Plan Expires", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def extract_accredited(text: str) -> Optional[bool]:
    match = re.search(r"NJUCF\s+Accredited:[\s\S]*?(Yes|No)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower() == "yes"
    return None


def parse_pdf(pdf_path: Path) -> List[Dict]:
    reader = PdfReader(str(pdf_path))
    report_year = None
    year_match = re.search(r"(20\d{2})", pdf_path.stem)
    if year_match:
        report_year = int(year_match.group(1))

    entries: List[Dict] = []
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        header = extract_header(text)
        updated = extract_updated(text)
        plan_year = extract_plan_year(text)
        accredited = extract_accredited(text)

        if not header.get("municipality"):
            continue

        entries.append(
            {
                "municipality": header["municipality"],
                "county": header["county"],
                "accredited": accredited,
                "updated": updated,
                "plan_year": plan_year,
                "report_year": report_year,
                "pdf": str(pdf_path),
                "page": page_index + 1,
            }
        )
    return entries


def main():
    context_dir = Path(__file__).resolve().parent.parent / "context"
    pdfs = sorted(context_dir.glob("*.pdf"))
    all_entries: List[Dict] = []
    for pdf in pdfs:
        print(f"Processing {pdf}...")
        all_entries.extend(parse_pdf(pdf))
    data_path = Path(__file__).resolve().parent.parent / "data" / "reports.json"
    data_path.parent.mkdir(exist_ok=True, parents=True)
    with data_path.open("w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)
    print(f"Saved {len(all_entries)} entries to {data_path}")


if __name__ == "__main__":
    main()
