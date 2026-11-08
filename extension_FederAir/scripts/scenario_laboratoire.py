"""Scénario complet du laboratoire (équivalent de client_laboratoire.py du TP4).

Catalogue -> tests négatifs -> contrat -> paquet signé -> calcul SANS bruit
(attendu 16.2 / 7.8 / 8.4) -> calcul AVEC bruit -> falsification (403) -> rejeu (409).
"""
import sys
import requests
from _common import (ENVIRONMENT_URL, DATASET_ID, CONSUMER_ID, ENV_HEADERS,
                     create_contract, get_signed_packet, to_hospital_payload,
                     post_aggregate)

echecs = []


def verifier(libelle, attendu, recu):
    ok = attendu == recu
    if not ok:
        echecs.append(libelle)
    print(f"   {libelle} : attendu {attendu}, reçu {recu}  [{'OK' if ok else 'ECHEC'}]")


def negocier(purpose="research", dataset=DATASET_ID, cle=None):
    h = {"X-API-Key": cle} if cle else ENV_HEADERS
    return requests.post(
        f"{ENVIRONMENT_URL}/api/v1/contracts",
        json={"dataset_id": dataset, "consumer_id": CONSUMER_ID,
              "purpose": purpose, "permissions": ["read_classifications"]},
        headers=h, timeout=10)


print("1. Découverte du catalogue")
r = requests.get(f"{ENVIRONMENT_URL}/api/v1/catalog", timeout=10)
r.raise_for_status()
print("  ", r.json()["catalog"][0]["title"])

print("\n2. Tests négatifs (gouvernance)")
verifier("Finalité commerciale", 403, negocier("commercial").status_code)
verifier("Jeu de données inexistant", 404, negocier(dataset="dataset-inconnu").status_code)
verifier("Clé API incorrecte", 401, negocier(cle="mauvaise-cle").status_code)

print("\n3. Contrat pour la recherche")
contract_id = create_contract()
print("   Contrat :", contract_id)

print("\n4. Paquet signé")
packet = get_signed_packet(contract_id)
print("   Jours classifiés :", packet["total"])

print("\n5. Calcul SANS bruit")
r = post_aggregate(to_hospital_payload(packet, apply_dp=False))
r.raise_for_status()
res = r.json()["results"]
hi, lo = res["HIGH"]["average_admissions"], res["LOW"]["average_admissions"]
print(f"   HIGH : n={res['HIGH']['days']} moyenne={hi}")
print(f"   LOW  : n={res['LOW']['days']} moyenne={lo}")
print(f"   Différence : {hi - lo:.2f}")
verifier("Moyenne HIGH (81/5)", 16.2, hi)
verifier("Moyenne LOW (39/5)", 7.8, lo)

print("\n6. Calcul AVEC bruit de Laplace (epsilon = 1)")
r = post_aggregate(to_hospital_payload(get_signed_packet(contract_id),
                                       apply_dp=True, epsilon=1.0))
r.raise_for_status()
bruit = r.json()["results"]
print(f"   HIGH : {bruit['HIGH']['average_admissions']}  LOW : {bruit['LOW']['average_admissions']}")

print("\n7. Test négatif : classifications falsifiées (sous-ensemble choisi par le labo)")
faux = get_signed_packet(contract_id)
faux["classifications"] = faux["classifications"][:4]
verifier("Signature falsifiée", 403, post_aggregate(to_hospital_payload(faux)).status_code)

print("\n8. Test négatif : rejeu du même paquet")
p = to_hospital_payload(get_signed_packet(contract_id))
post_aggregate(p)
verifier("Rejeu (nonce déjà utilisé)", 409, post_aggregate(p).status_code)

print("\nRÉSULTAT :", "tous les contrôles sont OK" if not echecs else f"ÉCHECS : {echecs}")
sys.exit(1 if echecs else 0)
