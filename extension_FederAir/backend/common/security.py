
import hashlib
import hmac
import json

def verify_api_key(received_key: str, expected_key: str) -> bool:
    """Compare deux clés sans comparaison ordinaire de chaînes."""
    if not received_key or not expected_key:
        return False

    return hmac.compare_digest(received_key, expected_key)



def sign_payload(
    contract_id: str,
    consumer_id: str,
    classifications: list[dict],
    timestamp: int,
    nonce: str,
    secret: str
) -> str:
    """Génère une signature HMAC-SHA256 du paquet fédéré."""

    message = json.dumps(
        {
            "contract_id": contract_id,
            "consumer_id": consumer_id,
            "classifications": classifications,
            "timestamp": timestamp,
            "nonce": nonce
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    return hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()


def verify_signature(
    signature: str,
    contract_id: str,
    consumer_id: str,
    classifications: list[dict],
    timestamp: int,
    nonce: str,
    secret: str
) -> bool:
    """Vérifie l'authenticité et l'intégrité du paquet."""

    expected = sign_payload(
        contract_id=contract_id,
        consumer_id=consumer_id,
        classifications=classifications,
        timestamp=timestamp,
        nonce=nonce,
        secret=secret
    )

    return hmac.compare_digest(signature, expected)
