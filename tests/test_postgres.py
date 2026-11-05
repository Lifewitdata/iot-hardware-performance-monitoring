"""Optional integration: set TEST_DATABASE_URL to a disposable PostgreSQL database."""
import os
import pandas as pd
import pytest
import psycopg
from src.config import SENSORS
from ingestion.load_sensor_data import load

def test_postgres_rerun_is_idempotent(tmp_path):
    dsn=os.getenv('TEST_DATABASE_URL')
    if not dsn: pytest.skip('TEST_DATABASE_URL is not configured')
    d=pd.DataFrame({'timestamp':pd.date_range('2099-01-01',periods=3,freq='10s')})
    for c in SENSORS: d[c]=0.
    path=tmp_path/'fixture.parquet'; d.to_parquet(path,index=False)
    try:
        n=load(path,dsn); assert load(path,dsn)==n
        with psycopg.connect(dsn) as conn:
            assert conn.execute("SELECT count(*) FROM sensor_readings WHERE timestamp>='2099-01-01' AND timestamp<'2099-01-02'").fetchone()[0]==3
    finally:
        with psycopg.connect(dsn) as conn:
            conn.execute("DELETE FROM sensor_readings WHERE timestamp>='2099-01-01' AND timestamp<'2099-01-02'")
