"""Utilitaires communs aux scripts FederAir (chemin du projet, création de contrat, paquet signé)."""
import sys
from pathlib import Path

# Permet de lancer : python scripts/xxx.py  (ou python -m scripts.xxx)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402
from backend.common.config import (  # noqa: E402
    ENVIRONMENT_API_KEY,
    HOSPITAL_API_KEY,
    FEDERATION_CONSUMER_ID,
)

ENVIRONMENT_URL = "http://127.0.0.1:8001"
HOSPITAL_URL = "http://127.0.0.1:8002"
DATASET_ID = "air-quality-pm25-tanger"
CONSUMER_ID = FEDERATION_CONSUMER_ID
ENV_HEADERS = {"X-API-Key": ENVIRONMENT_API_KEY}
HOSP_HEADERS = {"X-API-Key": HOSPITAL_API_KEY}


def create_contract(purpose="research", permissions=("read_classifications",)):
    """Crée un NOUVEAU contrat sur le nœud Environment et retourne son identifiant."""
    r = requests.post(
        f"{ENVIRONMENT_URL}/api/v1/contracts",
        json={"dataset_id": DATASET_ID, "consumer_id": CONSUMER_ID,
              "purpose": purpose, "permissions": list(permissions),
              "validity_days": 30},
        headers=ENV_HEADERS, timeout=10,
    )
    r.raise_for_status()
    return r.json()["contract"]["contract_id"]


def get_signed_packet(contract_id):
    """Récupère un paquet de classifications signé (nonce et timestamp neufs)."""
    r = requests.get(
        f"{ENVIRONMENT_URL}/api/v1/classifications",
        params={"contract_id": contract_id, "consumer_id": CONSUMER_ID,
                "purpose": "research"},
        headers=ENV_HEADERS, timeout=10,
    )
    r.raise_for_status()
    return r.json()


def to_hospital_payload(packet, **extra):
    """Construit le corps de POST /aggregate à partir du paquet signé."""
    payload = {k: packet[k] for k in
               ("contract_id", "consumer_id", "classifications",
                "timestamp", "nonce", "signature")}
    payload.update(extra)
    return payload


def post_aggregate(payload):
    return requests.post(f"{HOSPITAL_URL}/api/v1/aggregate",
                         json=payload, headers=HOSP_HEADERS, timeout=10)
