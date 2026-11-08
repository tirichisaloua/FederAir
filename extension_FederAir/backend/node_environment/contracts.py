
from datetime import datetime, timedelta, timezone
from uuid import uuid4


def create_contract(
    dataset_id: str,
    consumer_id: str,
    purpose: str,
    permissions: list[str],
    validity_days: int = 30
):
    """
    Crée un contrat simplifié d'utilisation d'un jeu de données.

    Le contrat est inspiré des principes d'ODRL.
    """

    now = datetime.now(timezone.utc)

    contract = {
        "contract_id": f"CONTRACT-{uuid4().hex[:12].upper()}",
        "dataset_id": dataset_id,
        "consumer_id": consumer_id,
        "purpose": purpose,
        "permissions": permissions,
        "created_at": now.isoformat(),
        "expires_at": (
            now + timedelta(days=validity_days)
        ).isoformat(),
        "status": "active"
    }

    return contract


def validate_contract(contract: dict, requested_purpose: str):
    """
    Vérifie si un contrat autorise l'utilisation demandée.
    """

    if contract["status"] != "active":
        return False

    expiration = datetime.fromisoformat(contract["expires_at"])

    if expiration <= datetime.now(timezone.utc):
        return False

    if contract["purpose"] != requested_purpose:
        return False

    return True
