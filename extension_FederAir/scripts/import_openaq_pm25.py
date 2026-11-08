"""Import daily PM2.5 measurements from OpenAQ v3 for a selected sensor.
Requires an OpenAQ API key. Use a sensor ID discovered from OpenAQ's locations/sensors endpoints.
"""
import argparse, os, requests, pandas as pd
from pathlib import Path

API="https://api.openaq.org/v3"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sensor-id",required=True,type=int)
    p.add_argument("--date-from",default="2020-01-01")
    p.add_argument("--date-to",default="2025-12-31")
    p.add_argument("--output",default="data/extended/environment/tangier_openaq_pm25.csv")
    a=p.parse_args()
    key=os.getenv("OPENAQ_API_KEY")
    if not key: raise SystemExit("OPENAQ_API_KEY is missing. Set it in your terminal environment.")
    headers={"X-API-Key":key,"Accept":"application/json"}
    rows=[]; page=1
    while True:
        url=f"{API}/sensors/{a.sensor_id}/days"
        r=requests.get(url,headers=headers,params={"date_from":a.date_from,"date_to":a.date_to,"limit":1000,"page":page},timeout=45)
        r.raise_for_status()
        payload=r.json(); batch=payload.get("results",[])
        if not batch: break
        rows.extend(batch)
        if len(batch)<1000: break
        page+=1
    if not rows: raise SystemExit("No daily observations returned. Check sensor ID, dates and API coverage.")
    df=pd.DataFrame(rows)
    # OpenAQ daily records typically contain period.datetimeFrom.utc and value.
    def date_of(row):
        period=row.get("period",{})
        return (period.get("datetimeFrom") or {}).get("utc") or row.get("datetime")
    df["date"]=df.apply(date_of,axis=1)
    df["date"]=pd.to_datetime(df["date"],utc=True,errors="coerce").dt.strftime("%Y-%m-%d")
    df["pm25_ug_m3"]=pd.to_numeric(df["value"],errors="coerce")
    df=df.dropna(subset=["date","pm25_ug_m3"]).groupby("date",as_index=False)["pm25_ug_m3"].mean()
    df["city"]="Tangier"
    df["data_origin"]="OPENAQ_OBSERVATION"
    df["sensor_id"]=a.sensor_id
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); df.to_csv(out,index=False)
    print(f"Saved {len(df)} daily PM2.5 observations to {out}")
    print("Verify location, station metadata, unit and license before using in scientific claims.")
if __name__=="__main__": main()
