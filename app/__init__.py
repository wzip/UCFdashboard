import json
import re
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "reports.json"
CONTEXT_DIR = BASE_DIR / "context"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_reports() -> List[Dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        entry["slug"] = slugify(entry["municipality"])
    return data


def build_app() -> Flask:
    app = Flask(__name__)

    reports = load_reports()
    counties = sorted({r.get("county") for r in reports if r.get("county")})
    years = sorted({r.get("report_year") for r in reports if r.get("report_year")})

    def filtered_reports(params: Dict[str, str]) -> List[Dict[str, Any]]:
        results = reports
        county = params.get("county")
        municipality = params.get("municipality")
        year = params.get("year")
        accredited = params.get("accredited")

        if county:
            results = [r for r in results if r.get("county") and r["county"].lower() == county.lower()]
        if municipality:
            results = [r for r in results if r.get("municipality") and r["municipality"].lower() == municipality.lower()]
        if year:
            try:
                year_int = int(year)
                results = [r for r in results if r.get("report_year") == year_int]
            except ValueError:
                pass
        if accredited:
            if accredited.lower() in {"true", "yes"}:
                results = [r for r in results if r.get("accredited") is True]
            elif accredited.lower() in {"false", "no"}:
                results = [r for r in results if r.get("accredited") is False]
        return results

    @app.route("/")
    def index():
        return render_template("index.html", counties=counties, years=years)

    @app.route("/municipality/<slug>")
    def municipality(slug: str):
        entries = [r for r in reports if r.get("slug") == slug]
        if not entries:
            abort(404)
        name = entries[0]["municipality"]
        display_entries: List[Dict[str, Any]] = []
        for entry in entries:
            display_entries.append({
                **entry,
                "pdf_url": f"/pdf/{Path(entry['pdf']).name}#page={entry['page']}",
            })
        return render_template(
            "municipality.html",
            municipality=name,
            entries=sorted(display_entries, key=lambda e: e.get("report_year", 0)),
        )

    @app.route("/api/meta")
    def meta():
        municipalities = sorted({r.get("municipality") for r in reports if r.get("municipality")})
        return jsonify({
            "counties": counties,
            "years": years,
            "municipalities": municipalities,
        })

    @app.route("/api/reports")
    def api_reports():
        results = filtered_reports(request.args)
        enriched = []
        for r in results:
            enriched.append({
                **r,
                "pdf_url": f"/pdf/{Path(r['pdf']).name}#page={r['page']}",
                "municipality_url": f"/municipality/{r['slug']}",
            })
        return jsonify(enriched)

    @app.route("/api/municipalities/<slug>")
    def api_municipality(slug: str):
        entries = [r for r in reports if r.get("slug") == slug]
        if not entries:
            abort(404)
        enriched = []
        for r in entries:
            enriched.append({
                **r,
                "pdf_url": f"/pdf/{Path(r['pdf']).name}#page={r['page']}",
                "municipality_url": f"/municipality/{r['slug']}",
            })
        return jsonify(enriched)

    @app.route("/pdf/<path:filename>")
    def pdf(filename: str):
        pdf_path = CONTEXT_DIR / filename
        if not pdf_path.exists():
            abort(404)
        return send_from_directory(CONTEXT_DIR, filename)

    return app


def main():
    app = build_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
