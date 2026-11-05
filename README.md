# IoT Hardware Performance Monitoring

An industrial sensor analytics project built around the MetroPT-3 air-compressor dataset. The project investigates compressor performance, sensor data quality, telemetry gaps, statistical and machine-learning anomaly detection, and reported failure intervals.

## Tableau Public dashboard

**[Open the IoT Hardware Performance Monitoring dashboard](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview)**

The dashboard is published on Tableau Public and provides the interactive visual view of the project.

## Project scope

The supplied project package contains Python data processing and validation, six analytical notebooks, anomaly-detection workflows, a Streamlit companion app, PostgreSQL schema and queries, processed monitoring datasets, figures, and verification reports.

## Dataset

The project uses the MetroPT-3 air-compressor dataset by Davari et al. (2021), available from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset), DOI 10.24432/C5VW3R, licensed under CC BY 4.0.

## Interpretation

The reported failure intervals are sparse maintenance/event records rather than ground-truth labels for every sensor reading. Alert evaluation is therefore proxy-based; anomalies should be treated as investigation leads, not confirmed faults or validated remaining-useful-life predictions.

---

**Repository publishing status:** The Tableau dashboard link and project overview are committed here. The source package and supporting project files have not yet been transferred into this GitHub repository.
