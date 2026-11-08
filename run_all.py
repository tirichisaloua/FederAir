"""Lance TOUT le projet automatiquement : TP1 -> TP2 -> TP3 -> TP4 -> extension_FederAir.

Pour chaque étape : crée les bases, démarre les API, exécute les clients/tests,
affiche les sorties, les enregistre dans rapport/resultats/ puis arrête les API.

Usage :
    python run_all.py              # tout
    python run_all.py TP3 TP4      # seulement certaines étapes (TP1 TP2 TP3 TP4 FEDERAIR)
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SORTIES = RACINE / "rapport" / "resultats"
PY = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
for var in ("CLE_ENVIRONNEMENT", "CLE_HOPITAL", "CLE_AIR", "SECRET_FEDERATION"):
    ENV.pop(var, None)  # on garde les valeurs de démonstration par défaut

ETAPES = {
    "TP1": dict(
        dossier="TP1",
        preparation=[["tp_federation.py"]],
        serveurs=[],
        clients=[["consulter_bases.py"]],
    ),
    "TP2": dict(
        dossier="TP2",
        preparation=[["creer_bases.py"]],
        serveurs=[("api_air:app", 8001), ("api_hopital:app", 8002)],
        clients=[["client_analyse.py"]],
    ),
    "TP3": dict(
        dossier="TP3",
        preparation=[["creer_bases.py"]],
        serveurs=[("api_air_v3:app", 8001), ("api_hopital_v3:app", 8002)],
        clients=[["laboratoire_v3.py"], ["attaque_difference.py"], ["tests_acces.py"]],
    ),
    "TP4": dict(
        dossier="TP4",
        preparation=[["setup_data.py"]],
        serveurs=[("api_air:app", 8001), ("api_hopital:app", 8002)],
        clients=[["client_laboratoire.py"], ["client_laboratoire.py", "--bruit"]],
    ),
    "FEDERAIR": dict(
        dossier="extension_FederAir",
        preparation=[["scripts/init_databases.py"], ["scripts/check_databases.py"]],
        serveurs=[("backend.node_environment.api:app", 8001),
                  ("backend.node_hospital.api:app", 8002)],
        clients=[["scripts/test_rest_communication.py"],
                 ["scripts/scenario_laboratoire.py"],
                 ["scripts/run_federated_analysis.py"],
                 ["scripts/run_federated_analysis.py", "--bruit"],
                 ["scripts/test_hmac_tampering.py"],
                 ["scripts/test_replay_attack.py"],
                 ["scripts/test_privacy_budget.py"]],
    ),
}


def port_ouvert(port):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def attendre(port, delai=30):
    fin = time.time() + delai
    while time.time() < fin:
        if port_ouvert(port):
            return True
        time.sleep(0.3)
    return False


def lancer(cmd, cwd, nom_sortie):
    r = subprocess.run([PY, *cmd], cwd=cwd, env=ENV, capture_output=True,
                       text=True, encoding="utf-8", timeout=120)
    texte = r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
    (SORTIES / f"{nom_sortie}.txt").write_text(texte, encoding="utf-8")
    return r.returncode, texte


def executer_etape(nom, cfg, resume):
    dossier = RACINE / cfg["dossier"]
    print("\n" + "#" * 70 + f"\n# {nom}\n" + "#" * 70)
    for port in (8001, 8002):
        if port_ouvert(port):
            print(f"!! Le port {port} est déjà utilisé : arrêtez l'autre serveur et relancez.")
            resume.append((nom, "ports occupés", False))
            return
    for cmd in cfg["preparation"]:
        code, out = lancer(cmd, dossier, f"{nom}_{Path(cmd[0]).stem}")
        print(f"\n$ python {' '.join(cmd)}  (code {code})\n{out.strip()}")
        resume.append((f"{nom} : {' '.join(cmd)}", f"code {code}", code == 0))
    serveurs = []
    try:
        for module, port in cfg["serveurs"]:
            p = subprocess.Popen(
                [PY, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port),
                 "--log-level", "warning"],
                cwd=dossier, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            serveurs.append(p)
            if not attendre(port):
                print(f"!! {module} n'a pas démarré sur le port {port}")
                resume.append((f"{nom} : démarrage {module}", "échec", False))
                return
        if serveurs:
            print(f"\n[API démarrées : {', '.join(f'{m} :{p}' for m, p in cfg['serveurs'])}]")
        for cmd in cfg["clients"]:
            suffixe = "_bruit" if "--bruit" in cmd else ""
            code, out = lancer(cmd, dossier, f"{nom}_{Path(cmd[0]).stem}{suffixe}")
            print(f"\n$ python {' '.join(cmd)}  (code {code})\n{out.strip()}")
            resume.append((f"{nom} : {' '.join(cmd)}", f"code {code}", code == 0))
    finally:
        for p in serveurs:
            p.terminate()
        for p in serveurs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        time.sleep(1)


def main():
    SORTIES.mkdir(parents=True, exist_ok=True)
    demandes = [a.upper() for a in sys.argv[1:]] or list(ETAPES)
    inconnues = [d for d in demandes if d not in ETAPES]
    if inconnues:
        sys.exit(f"Étapes inconnues : {inconnues}. Choix : {list(ETAPES)}")
    resume = []
    for nom in demandes:
        executer_etape(nom, ETAPES[nom], resume)
    print("\n" + "=" * 70 + "\nRÉSUMÉ\n" + "=" * 70)
    for libelle, detail, ok in resume:
        print(f"[{'OK   ' if ok else 'ECHEC'}] {libelle}  ({detail})")
    echecs = [r for r in resume if not r[2]]
    print(f"\n{len(resume) - len(echecs)}/{len(resume)} étapes réussies. "
          f"Sorties enregistrées dans {SORTIES}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
