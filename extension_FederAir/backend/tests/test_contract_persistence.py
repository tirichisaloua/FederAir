
from backend.node_environment.contracts import create_contract
from backend.node_environment.database import (
    init_database,
    save_contract,
    get_contract,
    revoke_contract
)

# 1. Initialiser la base
init_database()

# 2. Créer un contrat
contract = create_contract(
    dataset_id="air-quality-pm25-tanger",
    consumer_id="UNIVERSITY-LAB",
    purpose="research",
    permissions=["read_classifications"],
    validity_days=30
)

# 3. Enregistrer le contrat dans SQLite
save_contract(contract)

print("=== CONTRAT ENREGISTRÉ ===")
print(contract["contract_id"])

# 4. Récupérer le contrat depuis SQLite
saved_contract = get_contract(contract["contract_id"])

print("\n=== CONTRAT RÉCUPÉRÉ ===")
print(saved_contract)

# 5. Vérifier la persistance
assert saved_contract is not None
assert saved_contract["contract_id"] == contract["contract_id"]
assert saved_contract["permissions"] == ["read_classifications"]

print("\nTEST PERSISTANCE : RÉUSSI")

# 6. Révoquer le contrat
revoked = revoke_contract(contract["contract_id"])

print("\n=== RÉVOCATION ===")
print("Révocation effectuée :", revoked)

# 7. Vérifier son nouveau statut
updated_contract = get_contract(contract["contract_id"])

print("Nouveau statut :", updated_contract["status"])

assert updated_contract["status"] == "revoked"

print("\nTOUS LES TESTS SONT RÉUSSIS !")
