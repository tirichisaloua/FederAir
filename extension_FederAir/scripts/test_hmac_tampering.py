"""Test négatif : une classification modifiée après signature est rejetée (403)."""
import sys
from _common import create_contract, get_signed_packet, to_hospital_payload, post_aggregate

packet = get_signed_packet(create_contract())
payload = to_hospital_payload(packet)
original = payload["classifications"][0]["category"]
payload["classifications"][0]["category"] = "LOW" if original == "HIGH" else "HIGH"
r = post_aggregate(payload)
print("HTTP", r.status_code, r.text)
ok = r.status_code == 403 and "Invalid HMAC signature" in r.text
print("[PASS] Modification détectée." if ok else "[FAIL] Résultat inattendu.")
sys.exit(0 if ok else 1)
