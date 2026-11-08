"""Train two CPU-friendly demo models and export dashboard aggregates.
Hospital model uses a coarse HIGH/LOW pollution classification, not raw Environment data.
All hospital training targets in this demo are synthetic.
"""
from pathlib import Path
import json, warnings, os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"extended"
MODELS=ROOT/"models"
OUT=ROOT/"frontend"/"data"
OUT.mkdir(parents=True,exist_ok=True)

def features_environment(df):
    d=df.copy()
    d["date"]=pd.to_datetime(d["date"])
    d=d.sort_values("date").reset_index(drop=True)
    d["dayofweek"]=d.date.dt.dayofweek
    d["month"]=d.date.dt.month
    d["dayofyear"]=d.date.dt.dayofyear
    for col in ["pm25_ug_m3","pm10_ug_m3","no2_ug_m3","o3_ug_m3","temperature_c","relative_humidity_pct","wind_speed_ms"]:
        d[f"{col}_lag1"]=d[col].shift(1)
        d[f"{col}_rolling7"]=d[col].shift(1).rolling(7,min_periods=3).mean()
    return d

def metrics(y, pred):
    return {"mae":round(float(mean_absolute_error(y,pred)),3),
            "rmse":round(float(np.sqrt(mean_squared_error(y,pred))),3),
            "r2":round(float(r2_score(y,pred)),3)}

def train_one(X,y,model):
    split=int(len(X)*.8)
    pipe=Pipeline([("imputer",SimpleImputer(strategy="median", keep_empty_features=True)),("model",model)])
    pipe.fit(X.iloc[:split],y.iloc[:split])
    pred=pipe.predict(X.iloc[split:])
    return pipe, metrics(y.iloc[split:],pred), split, pred

def main():
    env_path=Path(os.getenv("FEDERAIR_ENVIRONMENT_CSV", str(DATA/"environment"/"tangier_environment_synthetic.csv")))
    hosp_path=Path(os.getenv("FEDERAIR_HOSPITAL_CSV", str(DATA/"hospital"/"tangier_hospital_synthetic.csv")))
    env=pd.read_csv(env_path)
    hosp=pd.read_csv(hosp_path)
    if "pm25_ug_m3" not in env.columns and "value" in env.columns:
        env=env.rename(columns={"value":"pm25_ug_m3"})
    for col in ["pm10_ug_m3","no2_ug_m3","o3_ug_m3","temperature_c","relative_humidity_pct","wind_speed_ms","precipitation_mm"]:
        if col not in env.columns: env[col]=np.nan
    if len(env)<180: raise SystemExit("At least 180 daily environment records are recommended for time-series model evaluation.")
    e=features_environment(env)
    env_cols=["pm25_ug_m3_lag1","pm25_ug_m3_rolling7","pm10_ug_m3_lag1","no2_ug_m3_lag1","o3_ug_m3_lag1","temperature_c","relative_humidity_pct","wind_speed_ms","precipitation_mm","dayofweek","month","dayofyear"]
    X=e[env_cols]; y=e["pm25_ug_m3"]
    def make_models():
        return {
            "RandomForest":RandomForestRegressor(n_estimators=160,max_depth=12,min_samples_leaf=3,n_jobs=-1,random_state=42),
            "HistGradientBoosting":HistGradientBoostingRegressor(max_iter=160,max_leaf_nodes=15,l2_regularization=1.0,random_state=42)
        }
    env_results={}
    env_pipes={}
    for name,model in make_models().items():
        pipe,m,split,pred=train_one(X,y,model); env_pipes[name]=pipe; env_results[name]=m
    best_env=min(env_results,key=lambda k:env_results[k]["mae"])
    MODELS.joinpath("environment").mkdir(parents=True,exist_ok=True)
    joblib.dump(env_pipes[best_env],MODELS/"environment"/"pm25_forecaster.joblib")

    # Hospital-local features: calendar, lags of admissions, and signed coarse pollution class.
    h=hosp.copy()
    h["date"]=pd.to_datetime(h.date)
    h=h.sort_values("date").reset_index(drop=True)
    pollution=env[["date","pm25_ug_m3"]].copy()
    pollution["date"]=pd.to_datetime(pollution["date"])
    h=h.merge(pollution,on="date",how="inner")
    h["pollution_class_high"]=(h["pm25_ug_m3"]>=30).astype(int)
    h["dayofweek"]=h.date.dt.dayofweek; h["month"]=h.date.dt.month; h["dayofyear"]=h.date.dt.dayofyear
    h["admissions_lag1"]=h.respiratory_admissions.shift(1)
    h["admissions_lag7"]=h.respiratory_admissions.shift(7)
    h["admissions_rolling7"]=h.respiratory_admissions.shift(1).rolling(7,min_periods=3).mean()
    hcols=["pollution_class_high","dayofweek","month","dayofyear","admissions_lag1","admissions_lag7","admissions_rolling7"]
    HX=h[hcols]; hy=h["respiratory_admissions"]
    hosp_results={}; hosp_pipes={}
    for name,model in make_models().items():
        pipe,m,split,pred=train_one(HX,hy,model); hosp_pipes[name]=pipe; hosp_results[name]=m
    best_hosp=min(hosp_results,key=lambda k:hosp_results[k]["mae"])
    MODELS.joinpath("hospital").mkdir(parents=True,exist_ok=True)
    joblib.dump(hosp_pipes[best_hosp],MODELS/"hospital"/"admissions_forecaster.joblib")

    # Prediction series on the chronological holdout for transparent visual evaluation.
    ep=e.iloc[int(len(e)*.8):].copy()
    ep_pred=env_pipes[best_env].predict(X.iloc[int(len(e)*.8):])
    hp=h.iloc[int(len(h)*.8):].copy()
    hp_pred=hosp_pipes[best_hosp].predict(HX.iloc[int(len(h)*.8):])
    env_month=env.assign(date=pd.to_datetime(env.date)).set_index("date").resample("MS").agg({"pm25_ug_m3":"mean","pm10_ug_m3":"mean","no2_ug_m3":"mean","o3_ug_m3":"mean"}).reset_index()
    hosp_month=hosp.assign(date=pd.to_datetime(hosp.date)).set_index("date").resample("MS").agg({"respiratory_admissions":"mean"}).reset_index()
    # Month-level aggregate association is illustrative and based on synthetic demo data.
    merged=env_month.merge(hosp_month,on="date")
    corr=float(merged[["pm25_ug_m3","respiratory_admissions"]].corr().iloc[0,1])
    payload={
      "metadata":{"city":"Tangier","period_start":str(env.date.min()),"period_end":str(env.date.max()),"days":len(env),"environment_origin":str(env.get("data_origin",pd.Series(["UNSPECIFIED"])).iloc[0]),"hospital_origin":str(hosp.get("data_origin",pd.Series(["UNSPECIFIED"])).iloc[0]),"note":"Check data_origin before interpretation. Hospital demo series is synthetic unless replaced by authorized, documented data."},
      "summary":{"pm25_mean":round(float(env.pm25_ug_m3.mean()),2),"pm25_p95":round(float(env.pm25_ug_m3.quantile(.95)),2),"pm10_mean":round(float(env.pm10_ug_m3.mean()),2),"admissions_mean":round(float(hosp.respiratory_admissions.mean()),2),"monthly_correlation":round(corr,3)},
      "environment_monthly":[{"month":r.date.strftime("%Y-%m"),"pm25":round(float(r.pm25_ug_m3),2),"pm10":round(float(r.pm10_ug_m3),2),"no2":round(float(r.no2_ug_m3),2),"o3":round(float(r.o3_ug_m3),2)} for r in env_month.itertuples()],
      "hospital_monthly":[{"month":r.date.strftime("%Y-%m"),"admissions":round(float(r.respiratory_admissions),2)} for r in hosp_month.itertuples()],
      "models":{"environment":{"best_model":best_env,"comparison":env_results,"target":"PM2.5 next-day value","test_days":len(ep),"actual":np.round(ep.pm25_ug_m3.to_numpy(),2).tolist(),"predicted":np.round(ep_pred,2).tolist(),"dates":ep.date.dt.strftime("%Y-%m-%d").tolist()},
                "hospital":{"best_model":best_hosp,"comparison":hosp_results,"target":"Synthetic daily respiratory admissions","test_days":len(hp),"actual":np.round(hp.respiratory_admissions.to_numpy(),2).tolist(),"predicted":np.round(hp_pred,2).tolist(),"dates":hp.date.dt.strftime("%Y-%m-%d").tolist()}},
      "quality":{"environment_missing":int(env.isna().sum().sum()),"hospital_missing":int(hosp.isna().sum().sum()),"environment_rows":len(env),"hospital_rows":len(hosp),"duplicate_environment_dates":int(env.date.duplicated().sum()),"duplicate_hospital_dates":int(hosp.date.duplicated().sum())}
    }
    (OUT/"dashboard.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    (MODELS/"training_report.json").write_text(json.dumps({"environment":env_results,"hospital":hosp_results,"best_environment":best_env,"best_hospital":best_hosp},indent=2),encoding="utf-8")
    print("Training complete.")
    print("Environment:",best_env,env_results[best_env])
    print("Hospital:",best_hosp,hosp_results[best_hosp])
    print("Dashboard data:",OUT/"dashboard.json")

if __name__=="__main__": main()
