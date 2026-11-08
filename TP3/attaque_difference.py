"""TP3 section 8 - Attaque par différence : le laboratoire choisit LUI-MÊME son groupe."""
import os
import requests

URL_HOPITAL = "http://127.0.0.1:8002"
CLE_HOPITAL = os.getenv("CLE_HOPITAL", "demo-hopital-456")

# Un seul jour : la "moyenne" est la valeur individuelle du 1er octobre.
demande = {"classifications": [{"date": "2026-10-01", "categorie": "non_elevee"}]}
r = requests.post(
    f"{URL_HOPITAL}/analyse-locale",
    headers={"X-API-Key": CLE_HOPITAL},
    json=demande,
    timeout=5,
)
print(r.json())
