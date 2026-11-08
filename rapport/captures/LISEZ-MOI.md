# Captures d'écran

Fichiers fournis (pris sur votre machine) :

| Fichier | Contenu |
|---|---|
| `01_installation_pip.png` | Installation des dépendances (`pip install -r requirements.txt`) |
| `02_swagger_noeud_A.png` | Swagger du nœud A (Environnement) |
| `03_swagger_noeud_B.png` | Swagger du nœud B (Hôpital) |
| `04_...` / `05_...` | Test 404 : jeu de données inexistant (requête et réponse) |
| `06_...` / `07_...` | Test 401 : clé API incorrecte (requête et réponse) |
| `08_...` / `09_...` | Test 403 : finalité `commercial` (requête et réponse) |
| `10_journal_uvicorn_noeud_A_TP4.png` | Journal du nœud A : 200, 403, 404, 401 |
| `11_TP3_run_all_attaque_difference_tests_acces.png` | TP3 : analyse, attaque par différence (8,0), 5 tests d'accès |
| `12_run_all_resume_20sur20.png` | Résumé de `python run_all.py` (20/20), reconstitué à partir du texte copié du terminal |
| `13_TP4_client_laboratoire_sans_bruit.png` | TP4 : `python client_laboratoire.py` — catalogue, 3 tests négatifs (403/404/401), contrat, 10 jours classifiés, moyennes 16,2 / 7,8, différence 8,40, signature falsifiée → 403 |
| `14_TP4_client_laboratoire_avec_bruit.png` | TP4 : `python client_laboratoire.py --bruit` — mêmes étapes, moyennes bruitées (24,17 / 0,0), signature falsifiée → 403 |

Les sorties texte complètes de chaque exécution sont dans `../resultats/`.

Facultatif : captures du tableau de bord (voir `README.md`, section « Tableau de bord »).
