"""Analyse fédérée complète : contrat -> paquet signé -> agrégation à l'hôpital."""
import requests
from _common import (create_contract, get_signed_packet, to_hospital_payload,
                     post_aggregate)


def display_results(results):
    print("\n" + "=" * 55)
    print("       FEDERAIR - FEDERATED ANALYSIS")
    print("=" * 55)
    print("Organisation :", results["organization"])
    print("Règle :", results["privacy_rule"])
    print("Bruit appliqué :", results["noise_applied"], "| epsilon :", results["epsilon"])
    for category, values in results["results"].items():
        print(f"\nCatégorie : {category}")
        print("  Statut :", values["status"])
        print("  Nombre de jours :", values["days"])
        if "average_admissions" in values:
            print("  Moyenne des admissions :", values["average_admissions"])


def main(apply_dp=False):
    try:
        print("[1/4] Création d'un contrat (finalité research)...")
        contract_id = create_contract()
        print("[OK] Contrat :", contract_id)
        print("[2/4] Récupération du paquet signé auprès d'Environment...")
        packet = get_signed_packet(contract_id)
        print("[OK] Classifications reçues :", packet["total"])
        print("[3/4] Transmission (inchangée) à Hospital...")
        r = post_aggregate(to_hospital_payload(packet, apply_dp=apply_dp, epsilon=1.0))
        r.raise_for_status()
        print("[4/4] Résultats")
        display_results(r.json())
    except requests.HTTPError as e:
        print("[ERREUR HTTP]", e.response.status_code, e.response.text)
    except requests.RequestException as e:
        print("[ERREUR] Communication impossible :", e)


if __name__ == "__main__":
    import sys
    main(apply_dp="--bruit" in sys.argv)
