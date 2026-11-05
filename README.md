# IoT Hardware Performance Monitoring

Real MetroPT-3 compressor readings, reproducible quality checks, six executed analytical notebooks, statistical/ML anomaly detectors and four engineering dashboard views.

**Live Tableau Public dashboard:** [Open the four-dashboard IoT Hardware Performance workbook](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview)

Open [START_HERE.html](START_HERE.html) for the illustrated offline report. Start with [the executed analysis report](reports/analysis_report.md), then open notebooks 01–06. Results are generated from the real CSV; synthetic values occur only in tests.

## Run locally (Python 3.11+)

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

The delivered processed datasets and Tableau-ready five-minute extract are included in `data/processed/`. The original raw sensor file is not included; obtain MetroPT-3 from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset) and place it at `data/raw/MetroPT3.csv` when you need to rerun the full pipeline.

```bash
python -m src.pipeline --csv data/raw/MetroPT3.csv
python -m pytest -q
streamlit run app/streamlit_app.py
```

The complete pipeline writes cleaned row-level Parquet, quarantine records, five-minute metrics, daily KPIs, model comparison, cycle details, event investigation, charts, report and fitted model. It is a batch historical monitor. JSONL replay demonstrates ingestion timing and is not an online model-serving system.

```bash
python -m ingestion.validate_sensor_data data/raw/MetroPT3.csv
python -m ingestion.streaming_simulator data/raw/MetroPT3.csv --limit 100 --delay 0.1
```

## PostgreSQL

Set `POSTGRES_PASSWORD` in a local `.env` copied from `.env.example`, then run `docker compose up -d`. Set `DATABASE_URL` in your shell; the Python loader does not load `.env` automatically.

```bash
# Bash
export DATABASE_URL='postgresql://metropt:YOUR_PASSWORD@localhost:5432/metropt'
# PowerShell equivalent: $env:DATABASE_URL='postgresql://metropt:YOUR_PASSWORD@localhost:5432/metropt'
python -m ingestion.load_sensor_data
```

The loader uses a transaction, temporary staging, PostgreSQL COPY and timestamp upserts. Rerunning the same input does not duplicate rows. SQL files contain monitoring, event and telemetry-gap queries. Set `TEST_DATABASE_URL` to a disposable database to run the integration test. See [reports/verification.md](reports/verification.md) for what was actually executed in this build.

## Tableau dashboard

The Tableau Public workbook is published here:

**[IoT Hardware Performance Monitoring — Tableau Public](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview)**

The included [Tableau guide](dashboards/tableau_guide.md) documents the dashboard data and build details. The published dashboard is the interactive, hosted visualization; the supporting analysis files and Tableau-ready extract are in this repository.

## Project navigation

- `ingestion/`: validate, load PostgreSQL, replay recorded telemetry.
- `src/`: preprocessing, causal features, six detectors, evaluation and reliability investigation.
- `notebooks/`: six notebooks with executed analysis, charts and interpretations.
- `data/reference/`: documented failure intervals.
- `data/processed/`: calculated outputs and Tableau-ready CSV/Parquet extracts.
- `sql/`: PostgreSQL schema and engineering queries.
- `app/`: Streamlit dashboard with performance, quality, anomaly and failure views.
- `reports/`: computed report, charts, data-quality audit and provenance.
- `tests/`: data integrity, leakage, event boundaries, app and optional database tests.
- `docs/`: dataset dictionary and methodology.
- `dashboards/`: Tableau data guide.

## Interpretation

February trains; March calibrates; April onward tests. Proxy precision/recall/F1 compare alerts with documented intervals, not complete ground truth. Outside-window alerts are not necessarily false. Reported event duration is not actual downtime. No MTBF, MTTR, RUL or deployment benefit is claimed without evidence. Flatline flags require engineering review.

Dataset attribution: Davari et al. (2021), [MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset), DOI 10.24432/C5VW3R, CC BY 4.0. Timestamps are kept in their original unspecified local timezone.

To rerun all six notebooks without a Jupyter server: `python scripts/execute_notebooks.py`. Exact packages used for the delivered run are in [requirements-lock.txt](requirements-lock.txt).
