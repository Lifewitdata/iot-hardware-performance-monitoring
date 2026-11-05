import numpy as np
import pandas as pd
import pytest
from src.config import ANALOG,DIGITAL
from src.preprocessing import clean_readings
from src.feature_engineering import aggregate_readings,label_events,assign_splits
from src.anomaly_detection import fit_and_score
from src.evaluation import evaluate
from src.reliability_analysis import operating_cycles

def fixture(n=500):
    d=pd.DataFrame({'timestamp':pd.date_range('2020-02-01',periods=n,freq='10s')})
    for c in ANALOG: d[c]=np.arange(n)*.01+1
    for c in DIGITAL: d[c]=0.
    return d

def test_duplicate_conflicts_quarantine_all_versions():
    d=fixture(); conflict=d.iloc[[1]].copy(); conflict['TP3']=999
    d=pd.concat([d,d.iloc[[0]],conflict],ignore_index=True)
    cleaned,q,r=clean_readings(d)
    assert r['exact_duplicates_removed']==1
    assert r['conflicting_timestamp_rows']==2
    assert len(cleaned)==499 and len(q)==2
    assert cleaned.timestamp.is_unique

def test_invalid_values_and_no_arbitrary_imputation():
    d=fixture(); d.loc[0,'timestamp']=pd.NaT; d.loc[1,'TP3']=np.inf; d.loc[2,'COMP']=3
    cleaned,q,r=clean_readings(d)
    assert len(q)==1
    assert r['numeric_coercions']['TP3']==1
    assert r['invalid_digital_values']['COMP']==1
    assert cleaned.TP3.isna().sum()==1
    assert cleaned.COMP.isna().sum()==1

def test_flatline_flags_reset_at_gaps():
    d=fixture(200); d['TP3']=1.; d.loc[100:,'timestamp']+=pd.Timedelta('1h')
    cleaned,_,r=clean_readings(d)
    assert cleaned.loc[90,'TP3_flatline']
    assert not cleaned.loc[100,'TP3_flatline']
    assert not cleaned.loc[150,'TP3_flatline']
    assert cleaned.loc[161,'TP3_flatline']

def test_aggregation_and_causal_features():
    d,_,r=clean_readings(fixture(3000)); x=aggregate_readings(d,10)
    changed=d.copy(); cut=pd.Timestamp('2020-02-01 04:00'); changed.loc[changed.timestamp>=cut,'TP3']+=1000
    y=aggregate_readings(changed,10)
    pd.testing.assert_frame_equal(x.loc[:cut],y.loc[:cut])
    assert x.iloc[0].sample_count==30
    assert x.iloc[0].availability==1
    assert x.loc['2020-02-01 01:05','TP3_rolling_mean']==pytest.approx(x.TP3.iloc[:12].mean())

def test_gap_bins_are_preserved():
    d=fixture(3000); d=d.drop(index=range(1000,2000)); d,_,_=clean_readings(d)
    x=aggregate_readings(d,10)
    assert (x.sample_count==0).any()
    assert not x.loc[x.sample_count==0,'quality_eligible'].any()

def test_event_boundary_and_chronological_split():
    ix=pd.to_datetime(['2020-04-18 00:00','2020-04-18 00:05','2020-04-19 00:05'])
    events=pd.DataFrame({'start':[pd.Timestamp('2020-04-18')],'end':[pd.Timestamp('2020-04-18 23:59')]})
    assert label_events(ix,events).tolist()==[False,True,False]
    assert assign_splits(pd.to_datetime(['2020-02-01','2020-03-01','2020-04-01'])).tolist()==['train','validation','test']

def test_test_data_does_not_change_fit_or_calibration():
    from src.feature_engineering import model_columns
    rng=np.random.default_rng(9)
    ix=pd.date_range('2020-02-01',periods=600,freq='5min')
    x=pd.DataFrame(rng.normal(size=(600,len(model_columns()))),columns=model_columns(),index=ix)
    for c in ANALOG: x[c+'_rolling_z']=rng.normal(size=600)
    x['quality_eligible']=True; x['split']=['train']*200+['validation']*200+['test']*200
    _,a,b=fit_and_score(x)
    y=x.copy(); y.loc[y.split.eq('test'),model_columns()]+=500
    _,a2,b2=fit_and_score(y)
    np.testing.assert_allclose(list(b['thresholds'].values()),list(b2['thresholds'].values()),rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(b['imputer'].statistics_,b2['imputer'].statistics_)
    pd.testing.assert_frame_equal(a.iloc[:400],a2.iloc[:400])

def test_event_metrics_do_not_count_missing_bins_as_negatives():
    ix=pd.date_range('2020-04-18',periods=6,freq='5min')
    x=pd.DataFrame({'split':'test','quality_eligible':[False,True,True,True,True,True],
        'event_window':[False,True,True,False,False,False]},index=ix)
    alerts=pd.DataFrame({'test_model':[True,True,False,False,True,True]},index=ix)
    e=pd.DataFrame({'event_id':['E'],'start':[ix[0]],'end':[ix[2]]})
    m,ev=evaluate(x,alerts,e)
    assert m.iloc[0].test_bins==5
    assert m.iloc[0].tp==1 and m.iloc[0].fp_proxy==2
    assert m.iloc[0].proxy_recall==.5
    assert ev.iloc[0].detected_during_event

def test_cycles_at_gap_are_censored():
    d=fixture(200); d['DV_eletric']=1; d.loc[100:,'timestamp']+=pd.Timedelta('1h')
    c=operating_cycles(d,10)
    assert len(c)==2 and c.censored.all()
    assert c.duration_seconds.max()==1000

def test_schema_missing_column_fails():
    with pytest.raises(ValueError,match='Missing required columns'): clean_readings(fixture().drop(columns='TP3'))


def test_simultaneous_flatline_bins_are_not_model_eligible():
    d=fixture(300)
    for c in ANALOG: d[c]=1.
    cleaned,_,_=clean_readings(d)
    x=aggregate_readings(cleaned,10)
    assert x.iloc[0].quality_eligible
    assert not x.iloc[-1].quality_eligible
