
from fastapi import FastAPI, Depends, Header, HTTPException
from typing import Optional, Literal
from pydantic import BaseModel, Field
import time
import numpy as np

from backend.common.config import (
    MIN_GROUP_SIZE,
    MAX_DAILY_ADMISSIONS,
    MAX_EPSILON_BUDGET
)
from backend.common.security import (
    verify_api_key,
    verify_signature
)
from backend.common.config import (
    HOSPITAL_API_KEY,
    FEDERATION_SECRET,
    FEDERATION_CONSUMER_ID
)
from backend.node_hospital.database import (
    init_database,
    get_all_admissions,
    register_nonce,
    consume_privacy_budget
)

class Classification(BaseModel):
    date: str
    category: Literal["HIGH", "LOW"]


class AggregationRequest(BaseModel):
    contract_id: str
    consumer_id: str
    classifications: list[Classification]
    timestamp: int
    nonce: str
    signature: str
    apply_dp: bool = False
    epsilon: float = Field(default=1.0, gt=0, le=MAX_EPSILON_BUDGET)


app = FastAPI(
    title="FederAir - Hospital Node",
    description="API REST de l'organisation hospitalière.",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    init_database()


def authenticate(
    x_api_key: Optional[str] = Header(default=None)
):
    """Authentification des requêtes adressées à l'hôpital."""

    if not verify_api_key(x_api_key, HOSPITAL_API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key."
        )

    return True


@app.get("/")
def root():
    return {
        "organization": "Hospital",
        "service": "FederAir Hospital Node",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "organization": "Hospital"
    }


@app.get(
    "/api/v1/admissions",
    dependencies=[Depends(authenticate)]
)
def get_admissions():
    """Route de consultation REST pour le TP 2."""

    admissions = get_all_admissions()

    return {
        "organization": "Hospital",
        "total": len(admissions),
        "data": admissions
    }


@app.get(
    "/api/v1/admissions/{admission_date}",
    dependencies=[Depends(authenticate)]
)
def get_admission(admission_date: str):
    """Récupère les admissions d'une date donnée."""

    admissions = get_all_admissions()

    for admission in admissions:
        if admission["date"] == admission_date:
            return admission

    raise HTTPException(
        status_code=404,
        detail="Admission record not found."
    )



@app.post("/api/v1/aggregate")
def aggregate_admissions(
    request: AggregationRequest,
    _: None = Depends(authenticate)
):

    # 2. Vérifier l'identité du consommateur
    if request.consumer_id != FEDERATION_CONSUMER_ID:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized consumer."
        )

    # 3. Convertir les classifications en dictionnaires
    classifications_data = [
        item.model_dump()
        for item in request.classifications
    ]

    # 4. Vérifier les dates du paquet
    dates = [item.date for item in request.classifications]

    if not dates:
        raise HTTPException(
            status_code=400,
            detail="Empty classification list."
        )

    if len(dates) != len(set(dates)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate classification dates."
        )

    # 5. Vérifier le format du nonce
    if not request.nonce or len(request.nonce) > 128:
        raise HTTPException(
            status_code=400,
            detail="Invalid nonce."
        )

    # 6. Vérifier la signature HMAC-SHA256
    valid_signature = verify_signature(
        signature=request.signature,
        contract_id=request.contract_id,
        consumer_id=request.consumer_id,
        classifications=classifications_data,
        timestamp=request.timestamp,
        nonce=request.nonce,
        secret=FEDERATION_SECRET
    )

    if not valid_signature:
        raise HTTPException(
            status_code=403,
            detail="Invalid HMAC signature. Request rejected."
        )

    # 7. Vérifier la fraîcheur du timestamp
    current_time = int(time.time())
    max_delay = 300

    if abs(current_time - request.timestamp) > max_delay:
        raise HTTPException(
            status_code=403,
            detail="Expired or invalid timestamp."
        )

    # 8. Vérifier que toutes les dates existent dans la base locale
    hospital_data = get_all_admissions()

    admissions_by_date = {
        record["date"]: record["number_of_admissions"]
        for record in hospital_data
    }

    unknown_dates = [d for d in dates if d not in admissions_by_date]

    if unknown_dates:
        raise HTTPException(
            status_code=400,
            detail=f"Dates absent from the hospital database: {unknown_dates}"
        )

    # 9. Enregistrer le nonce de manière atomique (anti-rejeu)
    nonce_registered = register_nonce(
        nonce=request.nonce,
        timestamp=request.timestamp
    )

    if not nonce_registered:
        raise HTTPException(
            status_code=409,
            detail="Replay attack detected. Nonce already used."
        )

    # 10. Préparer les groupes
    groups = {
        "HIGH": [],
        "LOW": []
    }

    for item in request.classifications:
        # Borne pédagogique du TP4
        bounded_value = min(
            admissions_by_date[item.date],
            MAX_DAILY_ADMISSIONS
        )
        groups[item.category].append(bounded_value)

    # 11. Groupes qui respectent le seuil minimal de publication
    eligible_groups = {
        category: values
        for category, values in groups.items()
        if len(values) >= MIN_GROUP_SIZE
    }

    # 12. Budget epsilon : consommé seulement si du bruit est demandé
    #     ET si au moins un résultat sera publié
    if request.apply_dp and eligible_groups:
        budget_available = consume_privacy_budget(
            contract_id=request.contract_id,
            epsilon=request.epsilon
        )

        if not budget_available:
            raise HTTPException(
                status_code=429,
                detail="Privacy budget exceeded."
            )

    # 13. Calculer les moyennes (exactes, ou bruitées si apply_dp)
    results = {}

    for category, values in groups.items():

        if len(values) < MIN_GROUP_SIZE:
            results[category] = {
                "status": "INSUFFICIENT_DATA",
                "days": len(values)
            }
            continue

        average = sum(values) / len(values)

        if request.apply_dp:
            sensitivity = MAX_DAILY_ADMISSIONS / len(values)
            scale = sensitivity / request.epsilon
            noise = np.random.laplace(loc=0, scale=scale)
            average = max(0, min(MAX_DAILY_ADMISSIONS, average + noise))

        results[category] = {
            "status": "OK",
            "days": len(values),
            "average_admissions": round(average, 2)
        }

    # 14. Retourner uniquement les résultats agrégés
    return {
        "organization": "Hospital",
        "privacy_rule": f"Minimum group size: {MIN_GROUP_SIZE}",
        "noise_applied": request.apply_dp,
        "epsilon": request.epsilon if request.apply_dp else None,
        "results": results
    }
