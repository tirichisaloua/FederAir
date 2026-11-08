"""Test : avec bruit et epsilon=1, le 4e appel dépasse le budget (3.0) -> 429."""
import sys
from _common import create_contract, get_signed_packet, to_hospital_payload, post_aggregate

contract_id = create_contract()
codes = []
for i in range(4):
    packet = get_signed_packet(contract_id)  # nonce neuf à chaque appel
    r = post_aggregate(to_hospital_payload(packet, apply_dp=True, epsilon=1.0))
    codes.append(r.status_code)
    print(f"Appel {i + 1} : HTTP {r.status_code}")
ok = codes == [200, 200, 200, 429]
print("[PASS] Budget épuisé au 4e appel (429)." if ok else f"[FAIL] Codes reçus : {codes}")
sys.exit(0 if ok else 1)
