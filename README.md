# Urban & Community Forestry Accreditation Dashboard

A lightweight Flask web application for browsing accreditation snapshots for New Jersey municipalities.
It surfaces data parsed from annual Urban & Community Forestry (UCF) accreditation reports and links each
result directly to the page in the source PDF. The dashboard exposes a searchable web UI as well as JSON
APIs that can be reused by other tools.

## How it works

- **Data extraction**: The `scripts/extract_reports.py` script reads PDF reports in the `context/` directory
  using `PyPDF2`, pulls out municipality, county, accreditation status, plan year, update date, and the
  report year inferred from the filename, then writes the consolidated dataset to `data/reports.json`.
- **Application**: `app/__init__.py` loads `reports.json`, builds common filter lists (counties, years),
  and exposes both HTML and JSON routes. PDFs in `context/` are served via `/pdf/<filename>` so the UI and
  API responses can link to the exact report page.
- **Frontend**: The `app/templates/index.html` template renders filters for county, municipality, year,
  and accreditation status. It calls `/api/reports` to show matching entries and links to municipality
  detail pages (`/municipality/<slug>`) and PDF anchors (`#page=<n>`).

Key routes:
- `/` – search dashboard UI.
- `/municipality/<slug>` – all records for a municipality.
- `/api/meta` – metadata for populating filters (counties, years, municipalities).
- `/api/reports` – filtered report data with links to PDFs and profiles.
- `/api/municipalities/<slug>` – records for a specific municipality.
- `/pdf/<filename>` – serves source PDFs stored in `context/`.

## Getting started locally

1. **Create a virtual environment and install dependencies** (Python 3.10+ recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Verify data and PDFs**: Ensure `data/reports.json` exists and that the referenced PDFs live in
   `context/`. If you add new PDFs or want to refresh the dataset, run:
   ```bash
   python scripts/extract_reports.py
   ```
3. **Run the development server**:
   ```bash
   flask --app app:build_app --debug run
   ```
   The site will be available at http://127.0.0.1:5000/.

## Using it as a web application

- **Production server**: Point a WSGI server like gunicorn at the factory `app:build_app`, e.g.:
  ```bash
  gunicorn --bind 0.0.0.0:8000 'app:build_app()'
  ```
  Serve the `context/` directory so `/pdf/<filename>` can return the source PDFs.
- **Static hosting setup**: Behind a reverse proxy (nginx/Apache), route application traffic to the
  WSGI server and allow direct access to `context/` for PDF downloads. Ensure the proxy forwards
  `X-Forwarded-Proto` headers if you terminate TLS upstream.
- **Refreshing data**: Place new yearly accreditation PDFs in `context/`, rerun `python scripts/extract_reports.py`,
  and redeploy or reload the WSGI process to pick up the updated `reports.json`.

## Project layout

- `app/__init__.py` – Flask application factory, routes, and filtering logic.
- `app/templates/` – HTML templates for the search page and municipality details.
- `app/static/` – Shared styling for the UI.
- `data/reports.json` – Parsed accreditation metadata.
- `context/` – Source accreditation report PDFs and related context files.
- `scripts/extract_reports.py` – PDF parser that regenerates `data/reports.json`.

## API quick start

Query the JSON API directly, for example:
```bash
curl 'http://127.0.0.1:5000/api/reports?county=Monmouth&accredited=true'
```
Each record includes `pdf_url` (link to the PDF page) and `municipality_url` (link to the municipality
summary page) to make integrating the data into other tools straightforward.
