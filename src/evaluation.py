import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

def evaluate(x,alerts,events):
    mask=x.split.eq('test') & x.quality_eligible
    y=x.event_window.astype(bool)
    metrics=[]; event_rows=[]
    for name in alerts:
        a=alerts[name].astype(bool)
        p,r,f,_=precision_recall_fscore_support(y[mask],a[mask],average='binary',zero_division=0)
        tn,fp,fn,tp=confusion_matrix(y[mask],a[mask],labels=[False,True]).ravel()
        unlabelled=mask & ~y
        starts=a & ~a.shift(1,fill_value=False)
        event_hits=[]
        for e in events.itertuples():
            inside=mask & (x.index>e.start) & ((x.index-pd.Timedelta('5min'))<=e.end)
            pre=mask & (x.index>=e.start-pd.Timedelta('24h')) & (x.index<=e.start) & ~y
            hit=a & inside; warning=a & pre
            first_warning=x.index[warning].min() if warning.any() else pd.NaT
            first_inside=x.index[hit].min() if hit.any() else pd.NaT
            observed=bool(inside.any())
            if observed: event_hits.append(bool(hit.any()))
            event_rows.append(dict(model=name,event_id=e.event_id,observed=observed,
                eligible_event_bins=int(inside.sum()),alert_bins=int(hit.sum()),
                detected_during_event=bool(hit.any()),first_event_alert=str(first_inside),
                warning_in_previous_24h=bool(warning.any()),first_warning=str(first_warning),
                lead_hours=(e.start-first_warning).total_seconds()/3600 if warning.any() else None))
        metrics.append(dict(model=name,proxy_precision=p,proxy_recall=r,proxy_f1=f,
            tp=int(tp),fp_proxy=int(fp),fn=int(fn),tn_proxy=int(tn),
            test_bins=int(mask.sum()),alert_bins=int(a[mask].sum()),
            alert_rate=float(a[mask].mean()),
            alerts_outside_documented_windows=int((a&unlabelled).sum()),
            outside_alert_episodes=int((starts&unlabelled).sum()),
            outside_episodes_per_observed_day=float((starts&unlabelled).sum()/max(unlabelled.sum()*5/1440,1e-9)),
            event_recall=float(np.mean(event_hits)) if event_hits else None))
    return pd.DataFrame(metrics),pd.DataFrame(event_rows)
