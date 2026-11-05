CREATE TABLE IF NOT EXISTS sensor_readings (
    timestamp timestamp PRIMARY KEY,
    tp2 double precision,
    tp3 double precision,
    h1 double precision,
    dv_pressure double precision,
    reservoirs double precision,
    oil_temperature double precision,
    motor_current double precision,
    comp double precision,
    dv_eletric double precision,
    towers double precision,
    mpg double precision,
    lps double precision,
    pressure_switch double precision,
    oil_level double precision,
    caudal_impulses double precision,
    CHECK (comp IN (0,1)), CHECK (dv_eletric IN (0,1)), CHECK (towers IN (0,1)),
    CHECK (mpg IN (0,1)), CHECK (lps IN (0,1)), CHECK (pressure_switch IN (0,1)),
    CHECK (oil_level IN (0,1)), CHECK (caudal_impulses IN (0,1))
);
CREATE TABLE IF NOT EXISTS failure_events (
    event_id text PRIMARY KEY, start_time timestamp NOT NULL,
    end_time timestamp NOT NULL, notes text, CHECK (end_time>=start_time)
);
CREATE INDEX IF NOT EXISTS sensor_readings_time_brin ON sensor_readings USING brin(timestamp);
