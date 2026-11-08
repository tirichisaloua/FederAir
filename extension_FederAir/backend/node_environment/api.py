
from fastapi import FastAPI, Depends, Header, HTTPException
from typing import Optional
from pydantic import BaseModel
import time
import uuid

from backend.common.config import ENVIRONMENT_API_KEY, PM25_THRESHOLD, FEDERATION_SECRET, FEDERATION_CONTRACT_ID, FEDERATION_CONSUMER_ID
from backend.common.security import verify_api_key, sign_payload
from backend.node_environment.database import (
    init_database,
    get_all_measurements,
    save_contract,
    get_contract,
    revoke_contract
)
from backend.node_environment.catalog import DATASET_CATALOG
from backend.node_environment.contracts import create_contract, validate_contract

class ContractRequest(BaseModel):
    dataset_id: str
    consumer_id: str
    purpose: str
    permissions: list[str]
    validity_days: int = 30

app = FastAPI(
    title="FederAir - Environment Node",
    description="API REST de l'organisation responsable des données environnementales.",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    init_database()


def authenticate(
    x_api_key: Optional[str] = Header(default=None)
):
    """Vérifie la clé API de l'organisation."""

    if not verify_api_key(x_api_key, ENVIRONMENT_API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key."
        )

    return True


@app.get("/")
def root():
    return {
        "organization": "Environment",
        "service": "FederAir Environment Node",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "organization": "Environment"
    }


@app.get(
    "/api/v1/measurements",
    dependencies=[Depends(authenticate)]
)
def get_measurements():
    """Consultation REST des mesures environnementales."""

    measurements = get_all_measurements()

    return {
        "organization": "Environment",
        "total": len(measurements),
        "data": measurements
    }


@app.get(
    "/api/v1/measurements/{measurement_date}",
    dependencies=[Depends(authenticate)]
)
def get_measurement(measurement_date: str):
    """Récupère une mesure pour une date donnée."""

    measurements = get_all_measurements()

    for measurement in measurements:
        if measurement["date"] == measurement_date:
            return measurement

    raise HTTPException(
        status_code=404,
        detail="Measurement not found."
    )



@app.get(
    "/api/v1/classifications",
    dependencies=[Depends(authenticate)]
)
def get_classifications(
    contract_id: str,
    consumer_id: str,
    purpose: str
):
    """
    Vérifie le contrat, génère les classifications
    et signe le paquet avant sa transmission.
    """

    # 1. Récupérer le contrat
    contract = get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Contract not found."
        )

    # 2. Vérifier l'identité du laboratoire
    if contract["consumer_id"] != consumer_id:
        raise HTTPException(
            status_code=403,
            detail="Consumer not authorized for this contract."
        )

    # 3. Vérifier le jeu de données
    if contract["dataset_id"] != DATASET_CATALOG["dataset_id"]:
        raise HTTPException(
            status_code=403,
            detail="Contract does not authorize this dataset."
        )

    # 4. Vérifier la validité et la finalité
    if not validate_contract(contract, purpose):
        raise HTTPException(
            status_code=403,
            detail="Contract is invalid, expired or purpose not allowed."
        )

    # 5. Vérifier la permission
    if "read_classifications" not in contract["permissions"]:
        raise HTTPException(
            status_code=403,
            detail="Permission read_classifications not granted."
        )

    # 6. Générer les classifications
    measurements = get_all_measurements()

    classifications = []

    for measurement in measurements:
        category = (
            "HIGH"
            if measurement["pm25"] > PM25_THRESHOLD
            else "LOW"
        )

        classifications.append({
            "date": measurement["date"],
            "category": category
        })

    # 7. Générer le timestamp et le nonce
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())

    # 8. Signer les classifications avec HMAC-SHA256
    signature = sign_payload(
        contract_id=contract_id,
        consumer_id=consumer_id,
        classifications=classifications,
        timestamp=timestamp,
        nonce=nonce,
        secret=FEDERATION_SECRET
    )

    # 9. Retourner le paquet signé
    return {
        "organization": "Environment",
        "contract_id": contract_id,
        "consumer_id": consumer_id,
        "total": len(classifications),
        "classifications": classifications,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature
    }



@app.get("/api/v1/catalog")
def get_catalog():
    """
    Consulte le catalogue des jeux de données disponibles.
    Les métadonnées sont publiques, sans accès aux données brutes.
    """
    return {
        "organization": "Environment",
        "catalog": [DATASET_CATALOG]
    }


@app.post(
    "/api/v1/contracts",
    dependencies=[Depends(authenticate)]
)
def create_new_contract(request: ContractRequest):
    """Crée et enregistre un nouveau contrat."""

    # Vérifier que le jeu de données existe
    if request.dataset_id != DATASET_CATALOG["dataset_id"]:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # Vérifier que la finalité est autorisée
    if request.purpose not in DATASET_CATALOG["allowed_purposes"]:
        raise HTTPException(
            status_code=403,
            detail="Purpose not allowed."
        )

    if not request.permissions:
        raise HTTPException(
            status_code=400,
            detail="At least one permission is required."
        )

    if request.validity_days < 1 or request.validity_days > 365:
        raise HTTPException(
            status_code=400,
            detail="Validity must be between 1 and 365 days."
        )

    # Créer le contrat
    contract = create_contract(
        dataset_id=request.dataset_id,
        consumer_id=request.consumer_id,
        purpose=request.purpose,
        permissions=request.permissions,
        validity_days=request.validity_days
    )

    # Enregistrer dans SQLite
    save_contract(contract)

    return {
        "message": "Contract created successfully.",
        "contract": contract
    }


@app.get(
    "/api/v1/contracts/{contract_id}",
    dependencies=[Depends(authenticate)]
)
def consult_contract(contract_id: str):
    """Consulte un contrat enregistré."""

    contract = get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Contract not found."
        )

    return contract


@app.post(
    "/api/v1/contracts/{contract_id}/revoke",
    dependencies=[Depends(authenticate)]
)
def revoke_existing_contract(contract_id: str):
    """Révoque un contrat actif."""

    revoked = revoke_contract(contract_id)

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="Active contract not found."
        )

    return {
        "message": "Contract revoked successfully.",
        "contract_id": contract_id,
        "status": "revoked"
    }
