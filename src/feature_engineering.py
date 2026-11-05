import numpy as np
import pandas as pd
from src.config import ANALOG,DIGITAL

def aggregate_readings(df,cadence):
    d=df.set_index('timestamp')
    # Right labels: timestamp is the moment the completed interval becomes available.
    rs=d.resample('5min',closed='left',label='right')
    x=rs[ANALOG+DIGITAL].mean()
    x['sample_count']=rs.size()
    x['availability']=(x.sample_count/(300/cadence)).clip(upper=1)
    x['complete_sensor_fraction']=1-rs['quality_missing'].mean()
    for c in ANALOG:
        x[c+'_std']=rs[c].std()
        x[c+'_min']=rs[c].min(); x[c+'_max']=rs[c].max()
        x[c+'_flatline_fraction']=rs[c+'_flatline'].mean()
    x['load_fraction']=rs['DV_eletric'].mean()
    x['pressure_gap']=x.TP3-x.Reservoirs
    x['all_analog_flatline_fraction']=rs['all_analog_flatline'].mean()
    x['quality_eligible']=(x.availability>=.8)&(x.complete_sensor_fraction>=.95)&(x.all_analog_flatline_fraction<=.2)
    # Empty/poor bins reset rolling history, rather than bridging unobserved time.
    for c in ANALOG:
        s=x[c].where(x.quality_eligible)
        x[c+'_delta']=s.diff()
        x[c+'_rolling_mean']=s.shift(1).rolling(12,min_periods=12).mean()
        x[c+'_rolling_std']=s.shift(1).rolling(12,min_periods=12).std()
        x[c+'_rolling_z']=(s-x[c+'_rolling_mean'])/x[c+'_rolling_std'].replace(0,np.nan)
    return x

def model_columns():
    return ANALOG+['load_fraction','pressure_gap']+[c+'_std' for c in ANALOG]+[c+'_delta' for c in ANALOG]

def label_events(index,events):
    # A right-labelled bin represents [timestamp-5min,timestamp); interval overlap proxy.
    label=np.zeros(len(index),dtype=bool)
    for e in events.itertuples():
        label|=(index>e.start)&((index-pd.Timedelta('5min'))<=e.end)
    return label

def assign_splits(index):
    origin=index.min().normalize().replace(day=1)
    train_end=origin+pd.DateOffset(months=1)
    val_end=origin+pd.DateOffset(months=2)
    return np.where(index<train_end,'train',np.where(index<val_end,'validation','test'))
