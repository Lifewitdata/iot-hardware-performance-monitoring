from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import streamlit as st
from src.config import ROOT,ANALOG
st.set_page_config(page_title='Compressor monitoring',layout='wide')
st.title('Compressor performance monitoring')
st.caption('MetroPT-3 real sensor history. Alerts indicate unusual observations; they do not confirm hardware failure.')
@st.cache_data
def load():
    return pd.read_parquet(ROOT/'data/processed/monitoring_5min.parquet')
if not (ROOT/'data/processed/monitoring_5min.parquet').exists():
    st.info('Run python -m src.pipeline --csv data/raw/MetroPT3.csv first.'); st.stop()
d=load()
dates=st.sidebar.date_input('Date range',value=(d.index.min().date(),d.index.max().date()),min_value=d.index.min().date(),max_value=d.index.max().date())
if len(dates)!=2: st.info('Select a start and end date.'); st.stop()
x=d.loc[str(dates[0]):str(dates[1])]
models=[c.removesuffix('_alert') for c in d if c.endswith('_alert')]
model=st.sidebar.selectbox('Detector',models,index=models.index('isolation_forest'))
sensor=st.sidebar.selectbox('Sensor',ANALOG,index=1)
a,b,c,e=st.columns(4)
a.metric('Readings',f'{int(x.sample_count.sum()):,}')
b.metric('Mean sampling coverage',f'{x.availability.mean():.1%}')
c.metric('Alert bins',f'{int(x[model+"_alert"].sum()):,}')
e.metric('Eligible bins',f'{int(x.quality_eligible.sum()):,}')
t1,t2,t3,t4=st.tabs(['Performance','Data quality','Anomaly evaluation','Failure investigation'])
with t1:
    st.subheader(sensor+' — hourly means'); st.line_chart(x[sensor].resample('1h').mean())
    st.subheader('Loaded-state fraction'); st.line_chart(x.load_fraction.resample('1h').mean())
with t2:
    st.line_chart(x.availability.resample('1D').mean())
    st.caption('Coverage uses observed sampling cadence. Communication gaps are not equipment downtime.')
    st.dataframe(x[['sample_count','availability','complete_sensor_fraction','quality_eligible']].tail(1000))
with t3:
    st.line_chart(x[model+'_score'].resample('1h').max())
    st.dataframe(pd.read_csv(ROOT/'data/processed/model_comparison.csv'),hide_index=True)
    st.caption('Metrics below use the complete held-out test period, independent of the date filter. Precision/recall/F1 use documented intervals as proxy labels.')
    st.dataframe(x.loc[x[model+'_alert'],[sensor,model+'_score','event_window','split']].tail(500))
with t4:
    st.dataframe(pd.read_csv(ROOT/'data/reference/failure_events.csv'),hide_index=True)
    ev=pd.read_csv(ROOT/'data/processed/event_evaluation.csv')
    st.dataframe(ev[ev.model.eq(model)],hide_index=True)
    st.caption('Full-period event evaluation. Lead time uses the preceding 24 hours. Downtime, MTBF and MTTR require verified operating and repair logs.')
st.download_button('Download filtered five-minute data',x.to_csv().encode(),'monitoring_filtered.csv','text/csv')
