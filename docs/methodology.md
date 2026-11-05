# Analysis and validation design

## Seven modules
1. Data understanding: executed notebook 01, sensor summary, temporal distributions and data dictionary.
2. Ingestion: repeatable CSV validation, quarantining, Parquet outputs, atomic PostgreSQL COPY/upsert and JSONL replay.
3. Performance: notebook 03, pressure/current/temperature trends, loading duty, cycle durations, variability and sampling coverage.
4. Statistics: notebook 04, training z-scores, lagged rolling deviations, empirical limits, two-sided CUSUM and autocorrelation.
5. Machine learning: notebook 05, Isolation Forest and regularised multivariate Mahalanobis distance, frozen chronological evaluation.
6. Failure investigation: notebook 06, preceding-week comparisons, hourly-block bootstrap intervals, exploratory tests and event-level warnings.
7. Engineering dashboards and delivery: Streamlit four-tab app, Tableau-ready CSVs and workbook-building specification. The prompt lists six modules; delivery supplies the seventh.

## Leakage controls
February is the fitting period; March sets score thresholds at its 99th percentile. April onward is test. Event labels are used only for evaluation and the separate failure investigation. No random split, full-data scaling or retrospective interpolation. Model inputs include seven analog means, seven within-bin standard deviations, seven first differences, pressure difference and loaded duty. Current-bin features are available only once the bin completes. Lagged rolling metrics require twelve complete eligible predecessor bins. Models can score valid bins without these rolling metrics; rolling-z detection naturally has warm-up gaps.

A 200-tree Isolation Forest uses seed 42 and up to 2,048 samples per tree. Ledoit–Wolf covariance shrinks covariance estimates to handle correlated sensors. The imputer and scaler fit on training rows only. Threshold limits are empirical training quantiles, not safety limits. Z-score is a maximum across sensors, not a normality-based probability. CUSUM accumulates standardised deviations with drift 0.5, resets at unavailable data and after a score above 50, and is a heuristic persistent-shift detector rather than proof of a physical change point. Calibration uses no failure outcomes.

An alert requires a current threshold exceedance and one of the previous two bins also exceeding; all three bins must be quality eligible. No alerts bridge unavailable intervals. Bin counts and episode counts are separate. Episode starts are rising edges of persistent alerts.

## Evaluation meaning
Bin-level precision, recall and F1 compare with documented-window overlap proxies. All metrics exclude poor-quality test bins. Event recall counts reported test events with at least one in-window alert among events with observed eligible data. Detection lead time uses the first alert within 24 hours before the reported start. An alert inside the event is detection, not early prediction. A model with frequent alerts can appear to have good early-warning coverage by chance.

Outside-window episodes per observed day use eligible non-event bins × 5 minutes as denominator. This is an exposure-based alert rate, not a rate per full calendar day. Incomplete labels prevent a confirmed false-alarm rate. Reporting all detectors avoids claiming that the model with highest test F1 has independently validated superiority. Only four documented events means no strong fleet-level statistical claims.

Hourly-block bootstrap differences and Welch tests are exploratory. Benjamini–Hochberg adjustment covers all sensor/event comparisons. Hour blocks may retain autocorrelation; state mix, seasonal change and train operation are possible confounders. No root-cause confirmation or causal inference is claimed. Digital-state-conditioned summaries are included in notebook 03.

MTBF, MTTR, actual downtime and RUL are deliberately unavailable without verified operational exposure and repair records. Event duration is not downtime.

Simultaneous analog flatlining is handled as a separate telemetry-quality concern: bins with more than 20% of readings having all seven analog sensors unchanged for at least ten minutes are excluded from model fitting/evaluation. Single-sensor flags remain diagnostic. The persistence rule uses only elapsed past observations, not future run duration. This heuristic does not prove telemetry corruption.
