"""Atomic PostgreSQL load using a temporary staging table and idempotent upsert."""
import argparse,os
import pandas as pd
import psycopg
from psycopg import sql
from src.config import ROOT,SENSORS

def load(parquet,dsn):
    d=pd.read_parquet(parquet,columns=['timestamp']+SENSORS)
    cols=['timestamp']+[c.lower() for c in SENSORS]
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT/'sql/schema.sql').read_text())
            cur.execute('CREATE TEMP TABLE staged_readings (LIKE sensor_readings INCLUDING DEFAULTS) ON COMMIT DROP')
            statement=sql.SQL('COPY staged_readings ({}) FROM STDIN').format(sql.SQL(',').join(map(sql.Identifier,cols)))
            with cur.copy(statement) as copy:
                for row in d.itertuples(index=False,name=None):
                    copy.write_row(tuple(None if pd.isna(v) else v for v in row))
            updates=sql.SQL(',').join(sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(c),sql.Identifier(c)) for c in cols[1:])
            cur.execute(sql.SQL('INSERT INTO sensor_readings ({c}) SELECT {c} FROM staged_readings ON CONFLICT (timestamp) DO UPDATE SET {u}').format(c=sql.SQL(',').join(map(sql.Identifier,cols)),u=updates))
            events=pd.read_csv(ROOT/'data/reference/failure_events.csv',parse_dates=['start','end'])
            for e in events.itertuples():
                cur.execute('INSERT INTO failure_events VALUES (%s,%s,%s,%s) ON CONFLICT(event_id) DO UPDATE SET start_time=EXCLUDED.start_time,end_time=EXCLUDED.end_time,notes=EXCLUDED.notes',(e.event_id,e.start,e.end,e.notes))
            cur.execute('SELECT count(*) FROM sensor_readings'); count=cur.fetchone()[0]
    return count

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--parquet',default=str(ROOT/'data/processed/readings.parquet')); a=p.parse_args()
    dsn=os.getenv('DATABASE_URL')
    if not dsn: raise SystemExit('Set DATABASE_URL to your PostgreSQL connection string')
    print(f'Rows in PostgreSQL: {load(a.parquet,dsn):,}')
