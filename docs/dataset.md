# Dataset and column dictionary

Source: [UCI MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset), DOI 10.24432/C5VW3R. Davari, Veloso, Ribeiro and Gama (2021). Data license: CC BY 4.0. Accessed 5 November 2026. This project analyses the uploaded 2020 MetroPT-3 data, not the different 2022 MetroPT release.

| Column | Interpretation | Unit |
|---|---|---|
| timestamp | Recorded local time; timezone unspecified | datetime |
| TP2 | Compressor pressure | bar |
| TP3 | Pneumatic-panel pressure | bar |
| H1 | Separator-related pressure | bar |
| DV_pressure | Dryer pressure signal | bar |
| Reservoirs | Reservoir pressure | bar |
| Oil_temperature | Compressor oil temperature | °C |
| Motor_current | Motor phase current | A |
| COMP | Intake-valve electrical state | binary |
| DV_eletric | Loaded-operation control state | binary |
| Towers | Dryer tower selection | binary |
| MPG | Compressor starting control | binary |
| LPS | Low-pressure signal | binary |
| Pressure_switch | Dryer discharge signal | binary |
| Oil_level | Oil-level signal | binary |
| Caudal_impulses | Air-flow pulse signal | binary |

The leading unnamed/index column is an export identifier, not a sensor. Original `DV_eletric` spelling is preserved. Digital means in five-minute outputs represent the fraction of valid readings equal to one, not an additional analog measurement. Signal polarity must be checked against engineering records before operational use.

## Time and label interpretation
The source describes both original 1 Hz logging and 0.1 Hz released observations. This project measures cadence from timestamp differences. Coverage is calendar coverage, not scheduled-service availability. Five-minute bins are right-labelled: a 00:05 observation represents readings from 00:00 inclusive to 00:05 exclusive. First/last partial bins can have reduced coverage.

Four documented intervals are stored in `data/reference/failure_events.csv`; their overlap with five-minute intervals creates evaluation proxies. The source repeats a report number and gives an inconsistent maintenance date for the second interval. IDs E01–E04 are project identifiers. Maintenance notes are not used to infer downtime. Unlabelled periods are not guaranteed healthy.

## Cleaning
Invalid timestamps and all conflicting timestamp versions are quarantined. Exact duplicate records are removed. Non-numeric/infinite measurements and non-binary digital values become missing and are counted. Physical extremes are retained; no unsupported manufacturer ranges are imposed. Flatline diagnostics use ten-minute unchanged analog runs and reset across gaps greater than three inferred sampling intervals. Digital flatlines are not automatically faults.

No backfilling or future-value interpolation is used. Models use training-median imputation after aggregation. Bins below 80% sampling coverage or 95% complete records are ineligible for alerts. Observed raw and cleaned row counts, missingness and source checksum are recorded in the reports.

Simultaneous analog flatlining is handled as a separate telemetry-quality concern: bins with more than 20% of readings having all seven analog sensors unchanged for at least ten minutes are excluded from model fitting/evaluation. Single-sensor flags remain diagnostic. The persistence rule uses only elapsed past observations, not future run duration. This heuristic does not prove telemetry corruption.
