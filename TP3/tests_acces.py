"""TP3 section 7 - Les 5 tests du contrôle d'accès."""
import requests

URL_AIR = "http://127.0.0.1:8001"
URL_HOPITAL = "http://127.0.0.1:8002"
BONNE_AIR, BONNE_HOP = "demo-air-123", "demo-hopital-456"
ok_global = True


def verifier(num, description, attendu, recu):
    global ok_global
    etat = "OK   " if attendu == recu else "ECHEC"
    ok_global &= attendu == recu
    print(f"Test {num} [{etat}] {description} : attendu {attendu}, reçu {recu}")


r = requests.get(f"{URL_AIR}/categories", timeout=5)
verifier(1, "/categories sans clé", 401, r.status_code)
r = requests.get(f"{URL_AIR}/categories", headers={"X-API-Key": "mauvaise"}, timeout=5)
verifier(2, "/categories clé incorrecte", 401, r.status_code)
r = requests.get(f"{URL_AIR}/categories", headers={"X-API-Key": BONNE_AIR}, timeout=5)
verifier(3, "/categories bonne clé", 200, r.status_code)
corps = {"classifications": r.json()}
r = requests.post(f"{URL_HOPITAL}/analyse-locale", json=corps,
                  headers={"X-API-Key": "mauvaise"}, timeout=5)
verifier(4, "/analyse-locale clé incorrecte", 401, r.status_code)
r = requests.post(f"{URL_HOPITAL}/analyse-locale",
                  json={"classifications": [{"date": "2026-10-01", "categorie": "inconnue"}]},
                  headers={"X-API-Key": BONNE_HOP}, timeout=5)
verifier(5, "catégorie inconnue", 400, r.status_code)
raise SystemExit(0 if ok_global else 1)
