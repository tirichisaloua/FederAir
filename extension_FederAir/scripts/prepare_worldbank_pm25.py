"""Normalize a World Bank city-level PM2.5 CSV after manual download/unzip.
Column names vary by release; pass them explicitly to avoid guessing.
"""
import argparse
from pathlib import Path
import pandas as pd

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True)
    p.add_argument("--date-column",required=True)
    p.add_argument("--city-column",required=True)
    p.add_argument("--value-column",required=True)
    p.add_argument("--city",default="Tangier")
    p.add_argument("--output",default="data/extended/environment/tangier_worldbank_pm25.csv")
    a=p.parse_args()
    df=pd.read_csv(a.input)
    required=[a.date_column,a.city_column,a.value_column]
    missing=[c for c in required if c not in df.columns]
    if missing: raise SystemExit(f"Missing columns {missing}. Available columns: {list(df.columns)}")
    out=df[df[a.city_column].astype(str).str.contains(a.city,case=False,na=False)].copy()
    out["date"]=pd.to_datetime(out[a.date_column],errors="coerce").dt.strftime("%Y-%m-%d")
    out["pm25_ug_m3"]=pd.to_numeric(out[a.value_column],errors="coerce")
    out=out.dropna(subset=["date","pm25_ug_m3"]).groupby("date",as_index=False)["pm25_ug_m3"].mean()
    out["city"]=a.city
    out["data_origin"]="WORLD_BANK_GLOBAL_PM25_MODEL_ESTIMATE"
    if out.empty: raise SystemExit(f"No rows found for {a.city}. Verify the city label and source file.")
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True);out.to_csv(dest,index=False)
    print(f"Prepared {len(out)} daily city-level PM2.5 estimates: {dest}")
    print("These are modelled city-level estimates, not direct station measurements.")
if __name__=="__main__":main()
