-- Telemetry gaps are not downtime.
WITH gaps AS (
 SELECT timestamp,timestamp-lag(timestamp) OVER(ORDER BY timestamp) AS gap
 FROM sensor_readings
)
SELECT count(*) FILTER(WHERE gap>INTERVAL '30 seconds') AS gap_count,
 max(gap) AS longest_gap FROM gaps;

-- Reported event duration, not repair time / MTTR / downtime.
SELECT event_id,extract(epoch FROM end_time-start_time)/3600.0 AS reported_event_hours,
 start_time-lag(start_time) OVER(ORDER BY start_time) AS elapsed_between_reported_starts
FROM failure_events ORDER BY start_time;
