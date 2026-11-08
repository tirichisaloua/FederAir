"""
Generate reproducible synthetic demonstration data for FederAir Health.
IMPORTANT: generated records are synthetic, not observations from real people or stations.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "extended"
RNG = np.random.default_rng(20261107)

def main():
    dates = pd.date_range("2019-01-01", "2025-12-31", freq="D")
    n = len(dates)
    doy = dates.dayofyear.to_numpy()
    dow = dates.dayofweek.to_numpy()
    t = np.arange(n)
    season = np.cos(2*np.pi*(doy-15)/365.25)
    trend = -0.0025*t
    temp = 19 + 8*np.sin(2*np.pi*(doy-105)/365.25) + RNG.normal(0,2.2,n)
    humidity = np.clip(67 - 12*np.sin(2*np.pi*(doy-100)/365.25) + RNG.normal(0,8,n),25,98)
    wind = np.clip(2.8 + 1.0*np.sin(2*np.pi*(doy+30)/365.25) + RNG.normal(0,.8,n),.2,9)
    rain = np.maximum(0, RNG.gamma(1.1,1.2,n) * (season>0.25))
    traffic = 1 + .12*np.sin(2*np.pi*dow/7) + RNG.normal(0,.07,n)
    pm25 = np.clip(17 + 6*season + 2.0*traffic - 1.25*wind - .12*rain + trend + RNG.normal(0,3.0,n), 2, 85)
    pm10 = np.clip(pm25*1.65 + RNG.normal(0,4,n), 4, 150)
    no2 = np.clip(13 + 7*traffic + 2*season - 1.1*wind + RNG.normal(0,2.5,n), 2, 65)
    o3 = np.clip(31 - 0.25*no2 + .45*temp + RNG.normal(0,4,n), 3, 100)
    env = pd.DataFrame({
        "date":dates.strftime("%Y-%m-%d"), "city":"Tangier",
        "pm25_ug_m3":pm25.round(2), "pm10_ug_m3":pm10.round(2),
        "no2_ug_m3":no2.round(2), "o3_ug_m3":o3.round(2),
        "temperature_c":temp.round(2), "relative_humidity_pct":humidity.round(2),
        "wind_speed_ms":wind.round(2), "precipitation_mm":rain.round(2),
        "traffic_index":traffic.round(3), "data_origin":"SYNTHETIC_DEMO"
    })
    # A synthetic hospital series with seasonality + a deliberately modest association with PM2.5.
    # It is not a clinical estimate and must never be represented as real admissions.
    winter = np.maximum(0,season)
    admissions = 11 + 4.0*winter + .13*pm25 + 1.5*(dow>=5) + RNG.normal(0,2.3,n)
    admissions = np.clip(np.rint(admissions),0,None).astype(int)
    hosp = pd.DataFrame({
        "date":env["date"], "city":"Tangier",
        "respiratory_admissions":admissions,
        "age_0_17":np.maximum(0,np.rint(admissions*.16+RNG.normal(0,.5,n))).astype(int),
        "age_18_64":np.maximum(0,np.rint(admissions*.51+RNG.normal(0,.8,n))).astype(int),
        "age_65_plus":np.maximum(0,np.rint(admissions*.33+RNG.normal(0,.7,n))).astype(int),
        "data_origin":"SYNTHETIC_DEMO"
    })
    (OUT/"environment").mkdir(parents=True,exist_ok=True)
    (OUT/"hospital").mkdir(parents=True,exist_ok=True)
    env.to_csv(OUT/"environment"/"tangier_environment_synthetic.csv",index=False)
    hosp.to_csv(OUT/"hospital"/"tangier_hospital_synthetic.csv",index=False)
    print(f"Generated {len(env)} daily environment rows and {len(hosp)} synthetic hospital rows.")
    print("All rows are explicitly labelled SYNTHETIC_DEMO.")

if __name__=="__main__": main()
