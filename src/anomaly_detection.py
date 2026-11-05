"""Fit on first calendar month; calibrate on second; freeze for remaining months."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.covariance import LedoitWolf
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from src.config import ANALOG,SEED
from src.feature_engineering import model_columns

def cusum_score(values,k=.5):
    pos=np.zeros(values.shape[1]); neg=pos.copy(); scores=[]
    for row in values:
        if not np.isfinite(row).all():
            pos[:]=0; neg[:]=0; scores.append(np.nan); continue
        pos=np.maximum(0,pos+row-k); neg=np.maximum(0,neg-row-k)
        scores.append(max(pos.max(),neg.max()))
        # Reset after large accumulation to permit repeated episodes.
        if scores[-1]>50: pos[:]=0; neg[:]=0
    return np.array(scores)

def fit_and_score(x):
    cols=model_columns()
    valid=x.quality_eligible & x[cols].notna().any(axis=1)
    train=valid & x.split.eq('train'); val=valid & x.split.eq('validation')
    if train.sum()<100 or val.sum()<100: raise ValueError('Need at least 100 eligible train and validation bins')
    imputer=SimpleImputer(strategy='median',keep_empty_features=True)
    scaler=StandardScaler()
    a=imputer.fit_transform(x.loc[train,cols]); a=scaler.fit_transform(a)
    all_a=scaler.transform(imputer.transform(x[cols]))
    forest=IsolationForest(n_estimators=200,max_samples=min(2048,len(a)),contamination='auto',random_state=SEED,n_jobs=-1).fit(a)
    covariance=LedoitWolf().fit(a)
    mu=x.loc[train,ANALOG].mean(); sd=x.loc[train,ANALOG].std().replace(0,np.nan)
    z=(x[ANALOG]-mu)/sd
    scores=pd.DataFrame(index=x.index)
    scores['zscore']=z.abs().max(axis=1)
    scores['rolling_z']=x[[c+'_rolling_z' for c in ANALOG]].abs().max(axis=1)
    scores['cusum']=cusum_score(z.where(valid).to_numpy())
    scores['isolation_forest']=-forest.score_samples(all_a)
    scores['mahalanobis']=covariance.mahalanobis(all_a)
    low=x.loc[train,ANALOG].quantile(.005); high=x.loc[train,ANALOG].quantile(.995)
    width=(high-low).replace(0,np.nan)
    scores['threshold']=pd.concat([(low-x[ANALOG])/width,(x[ANALOG]-high)/width],axis=1).max(axis=1)
    scores.loc[~valid,:]=np.nan
    thresholds={c:float(scores.loc[val,c].dropna().quantile(.99)) for c in scores}
    alerts=pd.DataFrame(index=x.index)
    for c in scores:
        raw=(scores[c]>thresholds[c]) & valid
        # Require current exceedance plus at least one prior exceedance in 3 eligible bins.
        contiguous=valid.rolling(3,min_periods=3).sum().eq(3)
        alerts[c]=raw & raw.rolling(3,min_periods=3).sum().ge(2) & contiguous
    bundle=dict(imputer=imputer,scaler=scaler,forest=forest,covariance=covariance,
        columns=cols,thresholds=thresholds,train_mean=mu,train_std=sd,quantile_low=low,quantile_high=high)
    return scores,alerts,bundle
