"""Test négatif : rejouer le même paquet (même nonce) est rejeté (409)."""
import sys
from _common import create_contract, get_signed_packet, to_hospital_payload, post_aggregate

payload = to_hospital_payload(get_signed_packet(create_contract()))
r1 = post_aggregate(payload)
r2 = post_aggregate(payload)
print("1re transmission :", r1.status_code, "| 2e transmission :", r2.status_code)
ok = r1.status_code == 200 and r2.status_code == 409
print("[PASS] Attaque par rejeu détectée." if ok else "[FAIL] Résultat inattendu.")
sys.exit(0 if ok else 1)
