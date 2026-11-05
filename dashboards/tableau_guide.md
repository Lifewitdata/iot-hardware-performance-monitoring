# Tableau dashboard specification

## What is published

The workbook `IoT_Hardware_Performance_Monitoring` is live on Tableau Public (author: Isfaque Ansari) and packaged here as [`IoT_Hardware_Performance_Monitoring.twbx`](IoT_Hardware_Performance_Monitoring.twbx) with its extract embedded.

| Published dashboard | Live view |
| --- | --- |
| 01 Compressor Overview | [open](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/01CompressorOverview) |
| 02 Sensor Monitoring | [open](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/02SensorMonitoring) |
| 03 Anomaly Investigation | [open](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/03AnomalyInvestigation) |
| 04 Data Quality | [open](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/IoT_Hardware_Performance_Monitoring/04DataQuality) |

The built layout differs from the original specification below: data-quality checks moved from `02` into their own `04 Data Quality`, `02` became per-signal monitoring, and `03` leads with rule-based flags. The specification is kept as the design record; the workbook is the delivered result.

Use Tableau Public Desktop. Connect to `data/processed/tableau_monitoring_5min.csv` and create an extract when publishing. Set timestamp to Date & Time. Add `daily_kpis.csv`, `model_comparison.csv` and `event_evaluation.csv` as separate sources to avoid duplicating five-minute rows.

## 01 Compressor Overview
KPI sheets: SUM(sample_count), AVG(availability), AVG(TP3), AVG(Oil_temperature). Hourly time-series sheets: pressure, temperature, current and load_fraction. Add timestamp date filter to all sheets using this source. Use line colour for event_window only as an event-context indicator, not a confirmed state classifier.

## 02 Sensor Data Quality
Plot availability by day, complete_sensor_fraction and analog flatline fractions. Show number of ineligible bins. Preserve empty time bins. Do not relabel availability as machine uptime.

## 03 Anomaly Monitoring
Chart isolation_forest_score against timestamp, overlay isolation_forest_alert as marks, and include a detail table of timestamp, TP3, Motor_current and event_window. Show model comparison from its separate source; these metrics cover the whole test period and must be labelled accordingly.

## 04 Failure Investigation
Use event_evaluation.csv with event_id/model filters. Show detected_during_event, eligible_event_bins, lead_hours and alert_bins. Add event_sensor_comparison.csv for before/event differences. Treat null lead_hours as no observed warning, never zero.

Suggested calculated fields:
- Alert bin: `IF [isolation_forest_alert] THEN 1 ELSE 0 END`
- Eligible bin: `IF [quality_eligible] THEN 1 ELSE 0 END`
- Mean pressure gap: `AVG([TP3]) - AVG([Reservoirs])`

Never SUM sensor means or proxy precision values. Keep reported event hours separate from downtime. Use 1400×900 dashboards, a neutral background, blue sensor traces and orange alerts. The `.twbx` in this folder is the built workbook behind the published views; this page records the design it was built from.
