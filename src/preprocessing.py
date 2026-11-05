"""Loss-aware cleaning; retain unusual physical values for investigation."""
import numpy as np
import pandas as pd
from src.config import SENSORS, ANALOG, DIGITAL

def clean_readings(raw):
    df = raw.copy()
    df.columns = df.columns.str.strip()
    df = df.rename(columns={'DV_electric':'DV_eletric','TOWERS':'Towers'})
    missing = set(['timestamp'] + SENSORS) - set(df.columns)
    if missing: raise ValueError(f'Missing required columns: {sorted(missing)}')
    df = df[['timestamp'] + SENSORS]
    original = len(df)
    df['timestamp'] = pd.to_datetime(df.timestamp, errors='coerce')
    invalid_time = df.timestamp.isna()
    quarantine = df.loc[invalid_time].copy()
    quarantine['reason'] = 'invalid_timestamp'
    df = df.loc[~invalid_time].copy()
    conversions = {}
    for c in SENSORS:
        old = df[c].notna()
        df[c] = pd.to_numeric(df[c], errors='coerce').replace([np.inf,-np.inf],np.nan)
        conversions[c] = int((old & df[c].isna()).sum())
    exact = df.duplicated(['timestamp']+SENSORS)
    exact_count = int(exact.sum())
    df = df.loc[~exact].copy()
    conflict = df.duplicated('timestamp',keep=False)
    # Quarantine every conflicting version rather than arbitrarily selecting a truth.
    q = df.loc[conflict].copy(); q['reason']='conflicting_timestamp'
    quarantine = pd.concat([quarantine,q],ignore_index=True)
    df = df.loc[~conflict].sort_values('timestamp').reset_index(drop=True)
    if len(df)<2: raise ValueError('At least two unique valid timestamps are required')
    digital_invalid = {}
    for c in DIGITAL:
        bad = df[c].notna() & ~df[c].isin([0,1])
        digital_invalid[c] = int(bad.sum()); df.loc[bad,c]=np.nan
    delta = df.timestamp.diff().dt.total_seconds()
    cadence = float(delta[delta>0].median())
    if cadence <= 0: raise ValueError('Nonpositive sampling cadence')
    df['gap_before_seconds'] = delta.fillna(0)
    df['quality_missing'] = df[SENSORS].isna().any(axis=1)
    frozen = {}
    # Flag unchanged analog runs >=10 min, reset at gaps; binary persistence is expected.
    for c in ANALOG:
        group = (df[c].ne(df[c].shift()) | (delta > 3*cadence) | df[c].isna()).cumsum()
        run_start = df.timestamp.groupby(group).transform('min')
        flag = ((df.timestamp-run_start).dt.total_seconds()>=600) & df[c].notna()
        df[c+'_flatline'] = flag
        frozen[c] = int(flag.sum())
    df['all_analog_flatline'] = df[[c+'_flatline' for c in ANALOG]].all(axis=1)
    report = dict(all_analog_flatline_rows=int(df.all_analog_flatline.sum()),raw_rows=original,clean_rows=len(df),invalid_timestamp_rows=int(invalid_time.sum()),
        exact_duplicates_removed=exact_count,conflicting_timestamp_rows=int(conflict.sum()),
        numeric_coercions=conversions,invalid_digital_values=digital_invalid,
        missing_by_sensor=df[SENSORS].isna().sum().astype(int).to_dict(),
        analog_flatline_flagged_rows=frozen,median_interval_seconds=cadence,
        p99_interval_seconds=float(delta.quantile(.99)),max_gap_seconds=float(delta.max()),
        gaps_over_3_cadences=int((delta>3*cadence).sum()),
        start=str(df.timestamp.min()),end=str(df.timestamp.max()))
    expected = (df.timestamp.max()-df.timestamp.min()).total_seconds()/cadence+1
    report['estimated_calendar_coverage']=min(1.,len(df)/expected)
    report['timestamp_interval_counts']=delta.value_counts().head(10).to_dict()
    return df,quarantine,report
