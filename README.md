# IoT Hardware Performance Monitoring

[![CI](https://github.com/Lifewitdata/iot-hardware-performance-monitoring/actions/workflows/ci.yml/badge.svg)](https://github.com/Lifewitdata/iot-hardware-performance-monitoring/actions/workflows/ci.yml)
![license: MIT](https://img.shields.io/badge/license-MIT-green)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

Condition monitoring for a real industrial air compressor, built on the **MetroPT-3** dataset: 1,516,948 sensor readings spanning 2020-02-01 to 2020-09-01.

The project covers the full path — ingestion, data-quality auditing, feature engineering, six anomaly detectors evaluated on a frozen chronological split, a failure investigation, a Streamlit app, PostgreSQL loading, and four published Tableau dashboards.

What makes it unusual is the discipline rather than the scope: event labels are used only for scoring, nothing is tuned on test data, and reliability numbers the data cannot support (MTBF, MTTR, downtime, RUL) are deliberately **not** reported. `START_HERE.html` is the illustrated offline version of this document.

## Live dashboards

Published on [Tableau Public](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview) as `IoT_Hardware_Performance_Monitoring` (Isfaque Ansari):

| Dashboard | What it answers |
| --- | --- |
| [01 Compressor Overview](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview) | Are pressure, temperature, current and load behaving normally over time? |
| [02 Sensor Monitoring](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/02SensorMonitoring) | Per-signal behaviour, including the share of digital readings equal to 1. |
| [03 Anomaly Investigation](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/03AnomalyInvestigation) | Which rule-based flags an engineer should actually open. |
| [04 Data Quality](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/04DataQuality) | Completeness, observation volume, missing fields and invalid digital values by day. |

[`dashboards/IoT_Hardware_Performance_Monitoring.twbx`](dashboards/IoT_Hardware_Performance_Monitoring.twbx) packages the same workbook with its extract embedded, so it opens in Tableau Desktop without regenerating any data. The design it was built from is in [`dashboards/tableau_guide.md`](dashboards/tableau_guide.md).

## What the analysis found

| Measurement | Result |
| --- | --- |
| Readings analysed | 1,516,948 over 7 months (median 10 s cadence, p99 12 s) |
| Calendar coverage | 82.36% — 331 gaps longer than three sampling intervals, longest 48.03 h |
| Five-minute bins model-eligible | 48,279 of 61,392 (≥80% coverage, ≥95% complete, <20% flatlined) |
| Observed operating means | 9.000 bar panel pressure, 62.64 °C oil temperature, 2.023 A motor current |
| Loaded-state runs | 15,539 complete runs, median 2.15 min |
| Suspect telemetry | 50,338 readings where all 7 analog sensors held identical for ≥10 min |

### Detector comparison (April onward, held out)

Precision, recall and F1 measure *agreement with the four documented event intervals*, not confirmed faults. An alert requires the current score to exceed its threshold **and** one of the two previous bins to exceed, with all three bins quality-eligible.

| Detector | Proxy precision | Proxy recall | Proxy F1 | Events detected | Outside-window episodes / observed day |
| --- | ---: | ---: | ---: | ---: | ---: |
| cusum | 0.607 | 0.936 | **0.736** | 75% | 0.12 |
| mahalanobis | 0.599 | 0.937 | 0.731 | 75% | 0.18 |
| threshold | 0.598 | 0.937 | 0.730 | 75% | 0.19 |
| zscore | 0.598 | 0.937 | 0.730 | 75% | 0.18 |
| isolation_forest | 0.045 | 0.001 | 0.002 | 25% | 0.18 |
| rolling_z | 0.000 | 0.000 | 0.000 | 0% | 0.00 |

The honest reading: the simple statistical detectors agreed with the documented intervals more often than the 200-tree Isolation Forest under this alert rule. That is a descriptive comparison on four events from one compressor — it is not evidence that a CUSUM beats unsupervised ML, and no production model is selected from it.

![Detector comparison](reports/figures/model_comparison.png)

### Sensor shift around documented failures

Each event is compared against the preceding seven days, excluding other events and poor-quality bins. Hourly-block bootstrap, 1,000 resamples, Welch tests with Benjamini–Hochberg correction. Exploratory association, not causal mechanism.

| Event | Panel pressure TP3 | Oil temperature | Motor current |
| --- | ---: | ---: | ---: |
| E01 | −0.246 bar | +16.32 °C | +3.67 A |
| E02 | −0.407 bar | +9.12 °C | +2.95 A |
| E03 | −1.026 bar | +10.93 °C | +3.57 A |
| E04 | −0.483 bar | +14.30 °C | +2.46 A |

Oil temperature and motor current rise in all four events while panel pressure falls — though for E04 the pressure interval crosses zero ([-1.345, +0.289]), so that one is not a resolved change. The four intervals total 87.48 h of **reported event exposure, not measured downtime**.

### Early warning is essentially absent

Across every detector and event, the longest lead time observed is **0.083 h (about 5 minutes)**, on E02. E03's first alert lands at 0.0 h — exactly at the reported start, which is detection, not prediction. No detector warned ahead of E01, and **E04 produced zero alert bins in every detector**. That 5-minute figure also deserves scepticism: these detectors fire in 281 of E01's 283 eligible bins, so background alerting alone can manufacture apparent lead time.

![Failure windows](reports/figures/failure_windows.png)

## How the evaluation stays honest

- **Chronological splits only.** February fits, March sets 99th-percentile score thresholds, April onward tests. No random split, no full-data scaling, no retrospective interpolation.
- **Causal features.** Rolling features use previous observations only; a bin's features exist only once the bin completes. Rolling-z therefore has natural warm-up gaps.
- **Labels never touch training.** Event intervals are used for scoring and the separate failure investigation only. Calibration uses no failure outcomes.
- **Quality gates before alerts.** Bins below 80% sampling coverage or 95% complete records are ineligible; alerts never bridge unavailable intervals.
- **Thresholds are empirical quantiles**, not manufacturer safety limits. Physical extremes are retained rather than clipped to unsupported ranges.
- **Downtime is not inferred.** Missing observations do not prove the machine was down, and event duration is not downtime.

Full design in [`docs/methodology.md`](docs/methodology.md); column-by-column definitions in [`docs/dataset.md`](docs/dataset.md).

## Project layout

```
ingestion/     validate CSV, load PostgreSQL, replay recorded telemetry as JSONL
src/           preprocessing, causal features, six detectors, evaluation, reliability
notebooks/     01–06, executed with charts and written interpretation
app/           Streamlit dashboard (performance, quality, anomaly, failure tabs)
dashboards/    published Tableau workbook (.twbx) + the specification it followed
sql/           PostgreSQL schema and engineering queries
data/          sample (committed), raw (git-ignored), reference intervals, processed outputs
reports/       computed report, figures, quality audit, run manifest, verification
tests/         integrity, leakage, event-boundary, app and optional DB tests
docs/          dataset dictionary and methodology
```

## Quick start (Python 3.11+)

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q                 # 12 passed, 1 skipped; green on a fresh clone
streamlit run app/streamlit_app.py  # opens against the committed sample
```

**The repository runs as cloned.** `data/sample/monitoring_5min_sample.parquet` (1.4 MB, 2020-04-15 to 2020-04-30, covering reported event E01) stands in for the full five-minute table, and the app captions which source it loaded. `pip install -e .` also works if you want `src` importable elsewhere.

For the complete seven months, download `MetroPT3(AirCompressor)(1).csv` from [UCI](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset), place it in `data/raw/` and rename it `MetroPT3.csv`. Check it against `reports/run_manifest.json` if you are reproducing the delivered numbers.

```bash
python -m src.pipeline --csv data/raw/MetroPT3.csv   # regenerates every figure and table above
```

Optional, without a Jupyter server: `python scripts/execute_notebooks.py` reruns all six notebooks. Exact packages for the delivered run are in `requirements-lock.txt`.

## Large files and Git

Generated outputs are git-ignored to keep the repository cloneable. `python -m src.pipeline` recreates all of them:

| File | Size | Needed for |
| --- | --- | --- |
| `data/raw/MetroPT3.csv` | ~66 MB | everything; download from [UCI](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset) |
| `data/processed/tableau_monitoring_5min.csv` | ~61 MB | reconnecting the workbook to live data |
| `data/processed/monitoring_5min.parquet` | ~20 MB | the Streamlit app |
| `models/detectors.joblib` | ~9 MB | reusing the fitted detectors |

`dashboards/IoT_Hardware_Performance_Monitoring.twbx` (~19 MB) is committed on purpose — it carries the embedded extract, which is the only way to open the dashboards offline.

## PostgreSQL

Set `POSTGRES_PASSWORD` in a local `.env` copied from `.env.example`, then `docker compose up -d`. Export `DATABASE_URL` yourself; the loader does not read `.env`.

```bash
# Bash
export DATABASE_URL='postgresql://metropt:YOUR_PASSWORD@localhost:5432/metropt'
# PowerShell
$env:DATABASE_URL='postgresql://metropt:YOUR_PASSWORD@localhost:5432/metropt'
python -m ingestion.load_sensor_data
```

Loading uses a transaction, temporary staging, PostgreSQL `COPY` and timestamp upserts, so rerunning the same input does not duplicate rows. Set `TEST_DATABASE_URL` to a disposable database to enable the integration test.

## What was actually verified

- Pipeline ran end to end on the real CSV; source SHA-256, split sizes and thresholds recorded in `reports/run_manifest.json`.
- All six notebooks executed — 30 cells, outputs saved.
- **12 passed, 1 skipped**, re-confirmed on Python 3.11 in an isolated environment — and re-run with the full Parquet removed, to prove the committed sample alone satisfies the app test.
- PostgreSQL 17.11 standalone: schema created, all 1,516,948 readings loaded, repeat upsert left the row count unchanged, every SQL query executed.
- Streamlit: `AppTest` exercised all four tabs, four KPI cards and both selectors without exceptions.
- Tableau workbook built and published; the four live views above were confirmed by rendering each one.
- `ruff check .` (rules E9, F) passes and `pip install -e .` resolves and imports.

GitHub Actions runs the linter, the suite and a **PostgreSQL 16 service** on every push. That service is the first-ever execution of the live psycopg connection path and of the image `docker-compose.yml` targets — this machine allows neither Docker nor outbound database sockets, so neither could be verified locally. Until the CI badge above is green, treat the integration test as unrun rather than passing. Details in [`reports/verification.md`](reports/verification.md).

## Limits you should read before quoting any number

Four documented events on one compressor cannot support fleet-level claims, and the event log may be incomplete. Outside-window alerts are *proxy* false positives, not confirmed false alarms. Unlabelled periods are not guaranteed healthy. Reported event duration is not downtime, and no MTBF, MTTR, RUL or cost benefit is estimated because verified operating hours and repair records are absent. Simultaneous analog flatlining is a telemetry concern with an unconfirmed cause — a constant sensor can be legitimate, especially a digital state. Timestamps keep their original unspecified local timezone.

Recommended next steps, in order: obtain shutdown/repair/operating-hour records, pilot alerts in shadow mode with an engineer-chosen alert budget, then validate on a later unseen period and additional equipment.

## Dataset and licence

Davari, Veloso, Ribeiro and Gama (2021). [MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset), UCI Machine Learning Repository, DOI 10.24432/C5VW3R, CC BY 4.0. This project analyses the 2020 MetroPT-3 release, not the different 2022 MetroPT data. The raw dataset is fetched from the source above; only aggregated derived outputs are committed here.

Code, notebooks and reports are [MIT](LICENSE) licensed. The dataset and its derivatives are **not** relicensed by that file — see the note at the end of `LICENSE`.

## Keywords

Hardware Data Analytics · IoT Sensor Data · Large-Scale Field Data · Sensor Data Monitoring · Data Ingestion · Data Processing · Data Storage · Reliable Data Pipelines · Data Quality · Hardware Performance Monitoring · Performance Metrics · Statistical Modelling · Machine Learning · Anomaly Detection · Trend Analysis · Time-Series Evaluation · Python · pandas · scikit-learn · SQL · PostgreSQL · Tableau · Python Visualisation · Performance Dashboards · Reporting · Data Storytelling · Actionable Insights · Data-Driven Recommendations

Deliberately absent: this project contains no firmware or software-version data, uses no AWS or QuickSight, involves no vehicle telematics, and does not compute MTBF, MTTR, uptime or remaining useful life — the source data cannot support those claims.
