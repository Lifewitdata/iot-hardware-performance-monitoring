import argparse,hashlib,json,platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import ROOT,ANALOG,SENSORS,SOURCE
from src.preprocessing import clean_readings
from src.feature_engineering import aggregate_readings,label_events,assign_splits
from src.anomaly_detection import fit_and_score
from src.evaluation import evaluate
from src.reliability_analysis import operating_cycles,event_comparisons

def run(csv):
    for p in ['data/processed','reports/figures','models']: (ROOT/p).mkdir(parents=True,exist_ok=True)
    out=ROOT/'data/processed'; reports=ROOT/'reports'
    print('Loading and validating raw CSV',flush=True)
    raw=pd.read_csv(csv)
    d,q,quality=clean_readings(raw); del raw
    d.to_parquet(out/'readings.parquet',index=False)
    flag=d.all_analog_flatline
    groups=(flag.ne(flag.shift()) | d.gap_before_seconds.gt(3*quality['median_interval_seconds'])).cumsum()
    flat=d.loc[flag].groupby(groups[flag]).agg(start=('timestamp','min'),end=('timestamp','max'),readings=('timestamp','size'))
    flat.to_csv(out/'simultaneous_flatline_episodes.csv',index=False)
    q.to_csv(out/'quarantine.csv',index=False)
    (reports/'data_quality.json').write_text(json.dumps(quality,indent=2))
    d[SENSORS].describe(percentiles=[.01,.05,.5,.95,.99]).T.to_csv(out/'sensor_summary.csv',index_label='sensor')
    events=pd.read_csv(ROOT/'data/reference/failure_events.csv',parse_dates=['start','end'])
    x=aggregate_readings(d,quality['median_interval_seconds'])
    x['split']=assign_splits(x.index)
    x['event_window']=label_events(x.index,events)
    print('Fitting detectors and frozen validation thresholds',flush=True)
    scores,alerts,bundle=fit_and_score(x)
    joblib.dump(bundle,ROOT/'models/detectors.joblib')
    metrics,event_eval=evaluate(x,alerts,events)
    metrics.to_csv(out/'model_comparison.csv',index=False)
    event_eval.to_csv(out/'event_evaluation.csv',index=False)
    comparison=event_comparisons(x,events)
    comparison.to_csv(out/'event_sensor_comparison.csv',index=False)
    cycles=operating_cycles(d,quality['median_interval_seconds'])
    cycles.to_csv(out/'operating_cycles.csv',index=False)
    for c in scores: x[c+'_score']=scores[c]; x[c+'_alert']=alerts[c]
    x.to_parquet(out/'monitoring_5min.parquet')
    x.reset_index().to_csv(out/'tableau_monitoring_5min.csv',index=False)
    daily=x.resample('1D').agg(sample_count=('sample_count','sum'),availability=('availability','mean'),
        eligible_bins=('quality_eligible','sum'),pressure=('TP3','mean'),temperature=('Oil_temperature','mean'),
        current=('Motor_current','mean'),load_fraction=('load_fraction','mean'),
        isolation_alert_bins=('isolation_forest_alert','sum'),event_bins=('event_window','sum'))
    daily.to_csv(out/'daily_kpis.csv',index_label='date')
    x[ANALOG].corr(method='spearman').to_csv(out/'sensor_correlations.csv',index_label='sensor')
    print('Rendering analysis charts',flush=True)
    sns.set_theme(style='whitegrid',palette='colorblind')
    fig,axs=plt.subplots(4,1,figsize=(13,10),sharex=True)
    for ax,c,title in zip(axs,['TP3','Oil_temperature','Motor_current','load_fraction'],['Panel pressure (bar)','Oil temperature (°C)','Motor current (A)','Loaded fraction']):
        x[c].resample('1h').mean().plot(ax=ax,lw=.8,color='#126782')
        for e in events.itertuples(): ax.axvspan(e.start,e.end,color='#d95d39',alpha=.25)
        ax.set_ylabel(title); ax.set_xlabel('')
    axs[0].set_title('Compressor performance — hourly means; reported leak windows shaded')
    fig.tight_layout(); fig.savefig(reports/'figures/performance.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,3.6)); daily.availability.plot(ax=ax,color='#126782')
    ax.set(title='Observed readings relative to estimated 10-second calendar cadence',ylabel='Coverage fraction',ylim=(0,1.05),xlabel='Date')
    fig.tight_layout(); fig.savefig(reports/'figures/availability.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,7)); sns.heatmap(x[ANALOG].corr(method='spearman'),annot=True,fmt='.2f',cmap='vlag',vmin=-1,vmax=1,ax=ax)
    ax.set_title('Sensor association — five-minute means (Spearman)'); fig.tight_layout(); fig.savefig(reports/'figures/correlations.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5)); metrics.set_index('model')[['proxy_precision','proxy_recall','proxy_f1']].plot.bar(ax=ax)
    ax.set(title='Held-out test: agreement with documented event windows',ylabel='Proxy metric',xlabel='',ylim=(0,1))
    plt.xticks(rotation=20,ha='right'); fig.tight_layout(); fig.savefig(reports/'figures/model_comparison.png',dpi=150); plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(13,8))
    for ax,e in zip(axs.flat,events.itertuples()):
        segment=x.loc[e.start-pd.Timedelta('2d'):e.end+pd.Timedelta('1d')]
        segment.TP3.plot(ax=ax,lw=.8); ax.axvspan(e.start,e.end,alpha=.2,color='#d95d39')
        ax.set(title=e.event_id+' — pressure around reported air leak',ylabel='TP3 (bar)',xlabel='')
    fig.tight_layout(); fig.savefig(reports/'figures/failure_windows.png',dpi=150); plt.close(fig)
    provenance=dict(input_name=Path(csv).name,input_sha256=hashlib.file_digest(open(csv,'rb'),'sha256').hexdigest(),
        source=SOURCE,python=platform.python_version(),pandas=pd.__version__,
        train_bins=int(x.split.eq('train').sum()),validation_bins=int(x.split.eq('validation').sum()),test_bins=int(x.split.eq('test').sum()),
        thresholds=bundle['thresholds'],seed=42,analysis_frequency='5min',timestamp_timezone='unspecified local time; no UTC conversion',
        run_utc=pd.Timestamp.now(tz='UTC').isoformat())
    (reports/'run_manifest.json').write_text(json.dumps(provenance,indent=2))
    generate_report(quality,x,metrics,event_eval,comparison,cycles,events)
    print(json.dumps(quality,indent=2)); print(metrics.to_string(index=False))
    return x

def generate_report(q,x,m,ev,comparison,cycles,events):
    # Build factual text directly from executed outputs; no fabricated benefits or failure labels.
    eligible=x.quality_eligible
    loaded=cycles.loc[cycles.load_state.eq(1)&~cycles.censored]
    best=m.sort_values('proxy_f1',ascending=False).iloc[0]
    all_hours=sum((e.end-e.start).total_seconds()/3600 for e in events.itertuples())
    lines=['# Hardware performance and failure investigation','',
        f"Analysed **{q['clean_rows']:,} readings**, from {q['start']} to {q['end']}. Input provenance and SHA-256 are in `run_manifest.json`.",'',
        '## Data quality and operating context',
        f"- Median sampling interval: {q['median_interval_seconds']:g} seconds; 99th percentile: {q['p99_interval_seconds']:g} seconds.",
        f"- {q['gaps_over_3_cadences']:,} gaps exceed three median sampling intervals. Longest gap: {q['max_gap_seconds']/3600:.2f} hours.",
        f"- Estimated coverage across the entire calendar span: {q['estimated_calendar_coverage']:.2%}. Missing observations do not prove equipment downtime.",
        f"- Removed {q['exact_duplicates_removed']:,} exact duplicates; quarantined {q['conflicting_timestamp_rows']:,} rows sharing conflicting timestamps and {q['invalid_timestamp_rows']:,} invalid timestamps.",
        f"- {int(eligible.sum()):,} of {len(x):,} five-minute bins meet at least 80% sampling coverage and 95% complete readings, with at most 20% of readings flagged for simultaneous analog flatlining.",
        f"- Complete loaded-state runs: {len(loaded):,}; median duration: {loaded.duration_seconds.median()/60:.2f} minutes. Runs at gaps and dataset boundaries are censored.",'',
        f"All seven analog sensors were simultaneously flatlined for at least ten minutes in {q['all_analog_flatline_rows']:,} readings. These are possible stale-telemetry episodes; their cause is unconfirmed. Bins with more than 20% such readings are excluded from model fitting and evaluation. See `simultaneous_flatline_episodes.csv`.",'',
        '## Performance',
        f"Eligible-bin mean panel pressure: {x.loc[eligible,'TP3'].mean():.3f} bar; oil temperature: {x.loc[eligible,'Oil_temperature'].mean():.2f} °C; motor current: {x.loc[eligible,'Motor_current'].mean():.3f} A.",
        'These are observed descriptive values, not manufacturer operating limits. Pressure differences and load duty are diagnostic context. Low negative pressure readings are retained because calibration offsets cannot be resolved from the CSV alone.','',
        '![Performance](figures/performance.png)','![Coverage](figures/availability.png)','',
        '## Chronological anomaly evaluation',
        'February fits the models; March calibrates the 99th-percentile score thresholds without event labels. April onward is held out. Alerts require the current score to exceed its threshold and at least one of the previous two scores to exceed; all three bins must be quality eligible. Rolling features use previous observations only.',
        'Precision, recall and F1 below measure agreement with reported event intervals. Outside-window alerts are proxy false positives, not confirmed false alarms. The event log may be incomplete. No test-set tuning is performed.','',
        '| Detector | Proxy precision | Proxy recall | Proxy F1 | Events detected | Outside-window episodes / observed day |',
        '|---|---:|---:|---:|---:|---:|']
    for row in m.itertuples():
        lines.append(f'| {row.model} | {row.proxy_precision:.3f} | {row.proxy_recall:.3f} | {row.proxy_f1:.3f} | {row.event_recall:.0%} | {row.outside_episodes_per_observed_day:.2f} |')
    lines += ['',f"The highest observed test proxy F1 is {best.proxy_f1:.3f} for {best.model}. This is a descriptive comparison, not a fresh independent validation of a selected production model.",
        '![Model comparison](figures/model_comparison.png)','',
        '## Documented failures and early warnings',
        f'The four reported intervals total {all_hours:.2f} hours. This is reported event exposure, **not measured downtime**. MTBF, MTTR, operational uptime and RUL are not estimated because verified operating-hours and repair/outage logs are absent.',
        'Early-warning lead time is measured from the first eligible alert in the preceding 24 hours to the reported start. Frequent background alerts can produce apparent lead time by chance; interpret with outside-window alert burden. See `event_evaluation.csv` for every detector and event.','',
        '| Event | IF detected during interval | IF alert bins | Prior-24h warning lead (hours) |',
        '|---|---|---:|---:|']
    for row in ev[ev.model.eq('isolation_forest')].itertuples():
        lead=f'{row.lead_hours:.2f}' if pd.notna(row.lead_hours) else 'No warning'
        lines.append(f'| {row.event_id} | {row.detected_during_event} | {row.alert_bins} | {lead} |')
    lines += ['','![Failure windows](figures/failure_windows.png)','',
        '## Sensor changes around failures',
        'Each event is compared with the preceding seven days, excluding other reported events and poor-quality bins. Hourly means are resampled 1,000 times for descriptive 95% bootstrap intervals; Welch tests and Benjamini–Hochberg corrections are exported. Hourly blocks can still be serially dependent and operating-state mix can confound differences. These are exploratory associations, not causal failure mechanisms.','',
        '| Event | Sensor | Baseline mean | Event mean | Difference | 95% descriptive interval |','|---|---|---:|---:|---:|---|']
    for row in comparison[comparison.sensor.isin(['TP3','Oil_temperature','Motor_current'])].itertuples():
        lines.append(f'| {row.event_id} | {row.sensor} | {row.baseline_mean:.3f} | {row.event_mean:.3f} | {row.difference:.3f} | [{row.bootstrap_low:.3f}, {row.bootstrap_high:.3f}] |')
    lines += ['','![Sensor correlations](figures/correlations.png)','',
        '## Engineering recommendations',
        '1. Review persistent pressure/current deviations alongside loaded-state duty and sensor agreement before opening a maintenance ticket.',
        '2. Check communication outages separately from mechanical failures; preserve unavailable bins in monitoring.',
        '3. Review flatline flags in operating context. A constant sensor can be legitimate, especially a digital state.',
        '4. Obtain verified shutdown, repair and operating-hour records before publishing reliability KPIs or confirmed false-alarm rates.',
        '5. Pilot alerts in shadow mode; have engineers label episodes and choose an alert budget before deployment.',
        '6. Validate on a later unseen period and additional equipment. Four events on one compressor do not establish fleet-level generalisation.','',
        '## Source and reproducibility',
        'Dataset: Davari et al. (2021), MetroPT-3, UCI Machine Learning Repository, DOI 10.24432/C5VW3R, CC BY 4.0.',
        'Source: '+SOURCE,
        'The source contains both 1 Hz logging and 0.1 Hz released-data descriptions. Analysis uses the measured cadence. Its E02 maintenance note is inconsistent and is excluded from repair/downtime calculations. Timestamps retain source-local interpretation because timezone is not specified.',
        'Run `python -m src.pipeline --csv data/raw/MetroPT3.csv` to regenerate all numbers and charts.']
    (ROOT/'reports/analysis_report.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--csv',required=True); args=p.parse_args(); run(args.csv)
