
from backend.node_environment.contracts import (
    create_contract,
    validate_contract
)


# 1. Création d'un contrat autorisant la recherche
contract = create_contract(
    dataset_id="air-quality-pm25-tanger",
    consumer_id="UNIVERSITY-LAB",
    purpose="research",
    permissions=["read_classifications"],
    validity_days=30
)

print("=== CONTRAT CRÉÉ ===")
print(contract)


# 2. Test avec la bonne finalité
print("\n=== TEST 1 : RESEARCH ===")
result = validate_contract(contract, "research")
print("Contrat accepté :", result)


# 3. Test avec une finalité non autorisée
print("\n=== TEST 2 : COMMERCIAL ===")
result = validate_contract(contract, "commercial")
print("Contrat accepté :", result)


# 4. Test avec un contrat désactivé
contract["status"] = "revoked"

print("\n=== TEST 3 : CONTRAT RÉVOQUÉ ===")
result = validate_contract(contract, "research")
print("Contrat accepté :", result)
