"""TP2 : communication REST avec les deux nœuds (santé + consultation des données brutes)."""
import sys
import requests
from _common import (ENVIRONMENT_URL, HOSPITAL_URL, ENV_HEADERS, HOSP_HEADERS)

ok = True
for nom, url in (("ENVIRONMENT", ENVIRONMENT_URL), ("HOSPITAL", HOSPITAL_URL)):
    r = requests.get(f"{url}/health", timeout=3)
    print(f"[{'ONLINE' if r.ok else 'OFFLINE'}] {nom}")
    ok &= r.ok

for nom, url, chemin, h in (
    ("ENVIRONMENT", ENVIRONMENT_URL, "measurements", ENV_HEADERS),
    ("HOSPITAL", HOSPITAL_URL, "admissions", HOSP_HEADERS),
):
    r = requests.get(f"{url}/api/v1/{chemin}", headers=h, timeout=5)
    r.raise_for_status()
    d = r.json()
    print(f"--- {nom} : {d['total']} enregistrements")
    for rec in d["data"]:
        print("   ", rec)
    ok &= d["total"] == 10
sys.exit(0 if ok else 1)
