# Project status - audit correction

The previous Git-only ZIP omitted the raw CSV and analysis exports. That package could not run immediately after extraction. The corrected full ZIP includes them in a single project folder. Install requirements first; Python dependencies are not bundled. GitHub tracking still excludes the large CSV.

The supplied Tableau workbook uses the raw sensor extract and rules (`TP3 < 7`, `Oil_level = 1`). It does **not** display the Python Isolation Forest alerts or the reported event intervals. The Python model metrics in the findings/PDF therefore do not measure the Tableau dashboard's flags. The preview PNGs are Python plots, not Tableau screenshots.

PostgreSQL code has not been exercised against a live database. Its loader currently appends to a fresh table and is not yet an idempotent production ingestion process. The notebooks and model are exploratory baselines; model comparison, validated lead time, and production deployment remain future work.

# IoT Hardware Performance Monitoring

An end-to-end sensor analytics project using the MetroPT-3 air-compressor dataset. It covers data understanding, validation, repeatable processing, hardware monitoring, statistical and machine-learning anomaly detection, and failure-window investigation. Alerts are investigation leads; the dataset does not provide row-level ground-truth labels.

**Tableau Public:** [Four-dashboard workbook](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview) · **Project report:** [PDF](reports/IoT_Hardware_Performance_Monitoring_Project_Report.pdf)

## What is in this repository

- `data/raw/`: source CSV (large; ~209 MB).
- `dashboards/hardware_performance.twbx`: packaged Tableau workbook with four dashboards and its embedded Hyper extract.
- `dashboards/screenshots/`: space for exported dashboard captures.
- `app/streamlit_app.py`: interactive local companion app for sensor exploration.
- `tests/`: focused tests for validation and reliability helpers.
- `reports/IoT_Hardware_Performance_Monitoring_Project_Report.pdf`: concise project and findings report.
- `data/reference/failure_events.csv`: four reported air-leak periods transcribed from the dataset documentation, with source caveats retained.
- `ingestion/`: loader, schema/quality validation, replay simulator, and analysis pipeline.
- `src/`: preprocessing, time-aware features, statistical/ML anomaly scoring, event evaluation, and reliability summaries.
- `notebooks/`: six focused analysis notebooks, from dataset understanding through event investigation.
- `sql/`: PostgreSQL schema and monitoring, anomaly, and reliability queries.
- `reports/generated/`: dashboard-ready hourly/minute, alert, event, and daily availability exports created by the pipeline.
- `reports/initial_findings.md`: first-pass findings calculated from the supplied CSV.
- `docs/`: sensor dictionary, methodology, caveats, and dashboard specification.

## Important dataset facts

The source CSV has **1,516,948 rows**, 17 source columns (a row index, timestamp, and 15 sensor signals), spans **2020-02-01 00:00:00 to 2020-09-01 03:59:50**, and contains no missing values or exact duplicate records. Timestamps are ordered and mostly 10 seconds apart; the supplied row index advances by 10. This is materially different from the PDF's stated 15,169,480 points at 1 Hz. The CSV therefore appears to be a ten-second sampled file, and contains occasional timestamp gaps. Use the CSV's observed timestamps for any interval or availability calculation; do not treat its row count as one-second coverage.

The first column (`Unnamed: 0`) is an exported index, not a sensor. The loader drops it while preserving the timestamp and all 15 signals. The source contains analog signals and binary/control signals; see `docs/data_dictionary.md`.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run the pipeline

From the repository root:

```bash
python ingestion/validate_sensor_data.py "data/raw/MetroPT3(AirCompressor).csv" --output data/processed/quality_report.json
python ingestion/load_sensor_data.py
python ingestion/run_analysis.py
```

The loader writes typed Parquet and CSV files plus a quality report. The analysis command creates one-minute monitoring data, statistical and Isolation Forest alert scores, daily coverage metrics, event-window summaries, and a JSON evaluation note. Outputs are ignored by Git so the source repository stays manageable. The source CSV is intentionally retained locally but ignored by Git because it exceeds GitHub's 100 MB single-file limit. Download the MetroPT-3 file from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt%2B3%2Bdataset) and place `MetroPT3(AirCompressor).csv` in `data/raw/`.

The model uses minute-level aggregates. The Isolation Forest's reference baseline ends before the first reported event. Statistical flags use trailing 30-minute z-scores and a 4 standard-deviation threshold. These are starting parameters for investigation, not validated operating limits. Event-window precision/recall depend on the chosen reported windows and one-hour lead allowance; they are not equivalent to verified failure classification metrics.

## PostgreSQL

Create a database, set `DATABASE_URL` (see `.env.example`), then execute `sql/schema.sql`. The optional `--postgres` flag on the loader writes the sensor readings to `monitoring.sensor_readings`:

```bash
python ingestion/load_sensor_data.py --postgres
```

The ingestion is designed for a fresh table. For repeated production loads, add an explicit upsert/checkpoint policy and an ingestion batch identifier before rerunning; do not append the complete history blindly.

## Streaming replay

The simulator replays historical records as JSON Lines, optionally sleeping between records:

```bash
python ingestion/streaming_simulator.py --limit 1000 --output data/processed/replay.jsonl
```

It is a local replay utility, not a live broker or production streaming system.

## Notebooks and dashboard

Start Jupyter from the repository root and run `notebooks/01_data_understanding.ipynb` through `06_failure_investigation.ipynb` in order. The Tableau dashboard layout, data sources, and KPI definitions are in `docs/dashboard_spec.md`; generated CSVs in `reports/generated/` are prepared for Tableau Public.

The four-dashboard Tableau workbook is also published on [Tableau Public](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview). Four static preview visuals are in `dashboards/screenshots/`; these are locally rendered previews from the same dataset. For the local companion app, run `streamlit run app/streamlit_app.py` from the project root. The app reads the same raw CSV; run the analysis pipeline first to populate its anomaly alert page.

Run the focused unit checks with `pytest -q`.

## Responsible interpretation

- Reported events are sparse maintenance/failure records, not labels for every sensor row.
- High-stress air-leak periods may explain some unusual behavior, but temporal association does not establish causality.
- Do not describe every model alert as a confirmed fault or claim predictive lead time without a defined event label, validated threshold, and time-based evaluation.
- The maintenance date shown for F2 in the source documentation appears earlier than that reported event; the reference file flags this for verification.
- The source spans into September 1 despite the general February–August description.

