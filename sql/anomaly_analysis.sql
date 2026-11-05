-- Descriptive per-event summaries; this does not assign confirmed failure labels to every row.
SELECT e.event_id,count(s.timestamp) AS readings,avg(s.tp3) AS mean_pressure,
 avg(s.oil_temperature) AS mean_oil_temperature,avg(s.motor_current) AS mean_current
FROM failure_events e LEFT JOIN sensor_readings s
 ON s.timestamp BETWEEN e.start_time AND e.end_time
GROUP BY e.event_id ORDER BY e.event_id;

-- Training-only reference limits, no test-set leakage.
WITH baseline AS (
 SELECT avg(tp3) AS mu,stddev_samp(tp3) AS sigma FROM sensor_readings
 WHERE timestamp>='2020-02-01' AND timestamp<'2020-03-01'
)
SELECT timestamp,tp3,(tp3-mu)/nullif(sigma,0) AS pressure_z
FROM sensor_readings CROSS JOIN baseline
WHERE timestamp>='2020-04-01' AND abs((tp3-mu)/nullif(sigma,0))>3;
