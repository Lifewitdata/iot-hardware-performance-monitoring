import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from src.config import ANALOG,SEED

def operating_cycles(df,cadence):
    d=df[['timestamp','DV_eletric','TP3','Motor_current']].copy()
    gaps=d.timestamp.diff().dt.total_seconds().gt(3*cadence)
    boundary=d.DV_eletric.ne(d.DV_eletric.shift())|gaps|d.DV_eletric.isna()
    group=boundary.cumsum()
    result=d.groupby(group).agg(start=('timestamp','min'),end=('timestamp','max'),
        load_state=('DV_eletric','first'),readings=('timestamp','size'),
        mean_pressure=('TP3','mean'),mean_current=('Motor_current','mean'))
    result['duration_seconds']=(result.end-result.start).dt.total_seconds()+cadence
    # Cycles touching a data gap or dataset edge are censored.
    censored_ids=set(group[gaps])|set(group.shift(1)[gaps].dropna().astype(int))|{int(group.iloc[0]),int(group.iloc[-1])}
    result['censored']=result.index.isin(censored_ids)
    return result.reset_index(drop=True)

def event_comparisons(x,events):
    rows=[]; rng=np.random.default_rng(SEED)
    for e in events.itertuples():
        during=x.loc[(x.index>e.start)&(x.index<=e.end)&x.quality_eligible]
        before=x.loc[(x.index>=e.start-pd.Timedelta('7d'))&(x.index<e.start)&x.quality_eligible&~x.event_window]
        for sensor in ANALOG:
            # Hour blocks reduce pseudo-replication; CIs remain descriptive, not causal.
            a=before[sensor].resample('1h').mean().dropna().to_numpy()
            b=during[sensor].resample('1h').mean().dropna().to_numpy()
            if min(len(a),len(b))<3: continue
            deltas=[rng.choice(b,len(b),replace=True).mean()-rng.choice(a,len(a),replace=True).mean() for _ in range(1000)]
            test=stats.ttest_ind(b,a,equal_var=False)
            rows.append(dict(event_id=e.event_id,sensor=sensor,baseline_hours=len(a),event_hours=len(b),
                baseline_mean=a.mean(),event_mean=b.mean(),difference=b.mean()-a.mean(),
                bootstrap_low=np.quantile(deltas,.025),bootstrap_high=np.quantile(deltas,.975),
                welch_p=float(test.pvalue)))
    result=pd.DataFrame(rows)
    if len(result): result['fdr_p']=multipletests(result.welch_p.fillna(1),method='fdr_bh')[1]
    return result
