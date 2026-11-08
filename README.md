# Rendu - Mini-espace de données fédéré (Santé et qualité de l'air)

## Contenu

| Dossier / fichier | Rôle |
|---|---|
| `run_all.py` | Lance tout automatiquement (voir ci-dessous) |
| `requirements.txt` | Dépendances Python |
| `TP1/` | Deux bases SQLite (5 jours) + consultation |
| `TP2/` | Deux API REST + client du laboratoire (données brutes) |
| `TP3/` | API protégées par clé, calcul local, attaque par différence, tests d'accès |
| `TP4/` | Gouvernance : catalogue, contrat, signature HMAC, seuil, bruit (conforme à l'énoncé, 10 jours) |
| `extension_FederAir/` | Extension facultative (contrats persistants, anti-rejeu, budget epsilon, tableau de bord web, ML) |
| `rapport/RAPPORT.md` | Réponses aux questions des 4 TP, calculs manuels, conclusion |
| `rapport/schema_architecture.png` | Schéma d'architecture (version `.svg` aussi) |
| `rapport/captures/` | Captures d'écran (liste dans `LISEZ-MOI.md`) |
| `rapport/resultats/` | Sorties texte de toutes les exécutions (générées par `run_all.py`) |

Les bases `.db` générées sont incluses dans chaque dossier.

## Lancer TOUT le projet (une seule commande)

Python 3.10 ou plus.

```bash
python -m venv .venv
# Windows PowerShell :  .\.venv\Scripts\Activate.ps1
# Linux / macOS     :  source .venv/bin/activate
python -m pip install -r requirements.txt

python run_all.py
```

`run_all.py` enchaîne TP1 → TP2 → TP3 → TP4 → FederAir : il crée les bases, démarre les API sur les ports 8001/8002, exécute les clients et les tests, enregistre les sorties dans `rapport/resultats/`, arrête les API, puis affiche un résumé (`20/20 étapes réussies`).

Une seule étape : `python run_all.py TP3` (choix : `TP1 TP2 TP3 TP4 FEDERAIR`).
Les ports 8001 et 8002 doivent être libres.

## Lancer chaque étape à la main (3 terminaux, venv activé dans chacun)

Remplacez `TPx` par le dossier voulu ; la première commande se lance une fois dans le terminal 3.

**TP1** : `cd TP1` puis `python tp_federation.py` puis `python consulter_bases.py`

**TP2** : `cd TP2`
- T3 : `python creer_bases.py`
- T1 : `python -m uvicorn api_air:app --port 8001`
- T2 : `python -m uvicorn api_hopital:app --port 8002`
- T3 : `python client_analyse.py`

**TP3** : `cd TP3` (clés de démonstration par défaut `demo-air-123` / `demo-hopital-456`)
- T3 : `python creer_bases.py`
- T1 : `python -m uvicorn api_air_v3:app --port 8001`
- T2 : `python -m uvicorn api_hopital_v3:app --port 8002`
- T3 : `python laboratoire_v3.py`, puis `python tests_acces.py`, puis `python attaque_difference.py`

**TP4** : `cd TP4` (sans `--reload`)
- T3 : `python setup_data.py`
- T1 : `python -m uvicorn api_air:app --port 8001`
- T2 : `python -m uvicorn api_hopital:app --port 8002`
- T3 : `python client_laboratoire.py` puis `python client_laboratoire.py --bruit`

**extension_FederAir** : `cd extension_FederAir` (les scripts se lancent aussi depuis la racine du rendu)
- T3 : `python scripts/init_databases.py` (facultatif : les API initialisent leurs bases au démarrage)
- T1 : `python -m uvicorn backend.node_environment.api:app --port 8001`
- T2 : `python -m uvicorn backend.node_hospital.api:app --port 8002`
- T3 : `python scripts/scenario_laboratoire.py` (scénario complet), puis au choix `scripts/run_federated_analysis.py [--bruit]`, `scripts/test_hmac_tampering.py`, `scripts/test_replay_attack.py`, `scripts/test_privacy_budget.py`, `scripts/test_rest_communication.py`

Interface web FederAir (facultatif, nécessite Node.js) : voir `extension_FederAir/README_FR.md` (Intelligence API sur 8003 et frontend sur 5500). Le « studio » demande toujours du bruit (`apply_dp: true`) ; le paramètre ε du curseur s'applique donc.

---

## Ce qui a été ajouté / modifié par rapport à vos zips

### Ajouté
1. **`TP1/`, `TP2/`, `TP3/`** : tous les fichiers Python du support (`tp_federation.py`, `consulter_bases.py`, API et client du TP 2, `api_air_v3.py`, `api_hopital_v3.py`, `laboratoire_v3.py`, `attaque_difference.py`) + `tests_acces.py` (les 5 tests de la section 7 du TP 3) + `creer_bases.py` dans TP2/TP3. Les chemins des bases sont relatifs au fichier, donc le lancement marche depuis n'importe quel dossier.
2. **`TP4/`** : les quatre fichiers de l'énoncé (`setup_data.py`, `api_air.py`, `api_hopital.py`, `client_laboratoire.py`), avec leurs bases générées. Le secret de démonstration est écrit `secret-federation-demo` (le PDF le coupe en fin de ligne).
3. **`extension_FederAir/scripts/scenario_laboratoire.py`** : scénario complet équivalent à `client_laboratoire.py` (catalogue, tests négatifs, contrat, calcul sans bruit 16,2/7,8, avec bruit, falsification, rejeu) avec vérifications automatiques.
4. **`extension_FederAir/scripts/_common.py`** : fonctions communes (création de contrat, paquet signé).
5. **`run_all.py`**, **`requirements.txt`** racine, **`rapport/RAPPORT.md`** (réponses, calculs manuels, conclusion), **`rapport/schema_architecture.png/.svg`**, **`rapport/resultats/`**, **`rapport/captures/LISEZ-MOI.md`**.

### Modifié (extension_FederAir)
1. **`backend/node_hospital/api.py`** :
   - ajout de `apply_dp: bool = False` : sans bruit par défaut (retrouve 16,2 et 7,8), bruit de Laplace seulement si `apply_dp = true` ; le budget epsilon n'est consommé que si du bruit est demandé ;
   - erreur 400 si la liste de classifications est vide ;
   - erreur 400 si une date est absente de la base hospitalière (avant l'enregistrement du nonce, pour ne pas le « brûler ») ;
   - la réponse indique `noise_applied` et `epsilon`.
2. **`frontend/app.js`** : le studio envoie `apply_dp: true` pour conserver son comportement bruité.
3. **Scripts** : `test_rest_communication.py` utilise maintenant les clés de `config.py` (il renvoyait 401) ; `run_federated_analysis.py`, `test_hmac_tampering.py`, `test_replay_attack.py`, `test_privacy_budget.py` créent leur propre contrat au lieu d'utiliser des `contract_id` écrits en dur ; `test_privacy_budget.py` fait 4 appels avec bruit (200, 200, 200, 429) ; `init_databases.py` et `check_databases.py` fonctionnent aussi avec `python scripts/xxx.py`.
4. **`.gitignore`** : les bases `.db` ne sont plus exclues.

### Ce qui reste à faire
- Relire `rapport/RAPPORT.md`, y mettre les noms, et le convertir au format demandé (Word ou PDF) en y insérant les captures de `rapport/captures/`.

---

## Tableau de bord web (extension_FederAir, facultatif)

Il s'agit d'une extension, non demandée par l'énoncé. Il faut **Node.js** (`node --version` doit répondre ; sinon installer la version LTS depuis https://nodejs.org). Les modèles ML et `frontend/data/dashboard.json` sont déjà inclus : il n'y a rien à entraîner.

Les ports 8001, 8002, 8003 et 5500 doivent être libres. Ouvrir **4 terminaux** (venv activé dans les trois premiers), tous depuis la racine du rendu :

| Terminal | Commandes |
|---|---|
| 1 - Environment | `cd extension_FederAir` puis `python -m uvicorn backend.node_environment.api:app --port 8001` |
| 2 - Hospital | `cd extension_FederAir` puis `python -m uvicorn backend.node_hospital.api:app --port 8002` |
| 3 - Intelligence API | `cd extension_FederAir` puis `python -m uvicorn backend.intelligence_api:app --port 8003` |
| 4 - Frontend | `cd extension_FederAir\frontend` puis `node server.mjs` |

Ouvrir http://127.0.0.1:5500 (workspace) et http://127.0.0.1:5500/advanced.html (studio analytique).

Dans « Configuration des connexions », saisir les clés de démonstration : `dev-environment-key` (Environment) et `dev-hospital-key` (Hospital).

Parcours à capturer : créer un contrat (consommateur `UNIVERSITY-LAB`, finalité `research`, permission `read_classifications`), lancer l'analyse fédérée (curseur ε), puis ouvrir le studio.

Arrêt : `Ctrl+C` dans chaque terminal.
