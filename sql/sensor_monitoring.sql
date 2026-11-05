-- PostgreSQL 14+. Coverage assumes measured 10-second cadence; calendar denominator.
SELECT date_trunc('day',timestamp) AS day, count(*) AS readings,
    avg(tp3) AS pressure_bar, min(tp3) AS minimum_pressure_bar, max(tp3) AS maximum_pressure_bar,
    stddev_samp(tp3) AS pressure_std, avg(oil_temperature) AS oil_temperature_c,
    avg(motor_current) AS motor_current_a, avg(dv_eletric) AS loaded_fraction,
    least(1.0,count(*)/8640.0) AS calendar_coverage
FROM sensor_readings GROUP BY 1 ORDER BY 1;

-- Time-based rolling statistic; current reading excluded.
SELECT timestamp,tp3,
 avg(tp3) OVER (ORDER BY timestamp RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND INTERVAL '1 microsecond' PRECEDING) AS trailing_pressure,
 tp3-lag(tp3) OVER(ORDER BY timestamp) AS pressure_step
FROM sensor_readings ORDER BY timestamp;
