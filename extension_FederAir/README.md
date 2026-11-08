# FederAir Health — Federated Environmental & Public Health Intelligence

**Projet Master IASD — plateforme de démonstration locale**

FederAir Health étudie les relations entre la qualité de l'air et la santé respiratoire à travers trois rôles :
- **Environment** : propriétaire des données environnementales.
- **Hospital** : propriétaire des données hospitalières et calculateur local.
- **University Lab** : consommateur autorisé de métadonnées et de résultats agrégés.

La règle architecturale centrale est : **les données détaillées restent dans l'organisation propriétaire ; seules des informations explicitement autorisées sont échangées.**

> **Important — provenance des données fournies :** le ZIP contient un jeu de démonstration reproductible de 2 557 jours, mais les deux séries incluses sont générées artificiellement et étiquetées `SYNTHETIC_DEMO`. Elles ne sont ni des observations réelles de Tanger, ni des dossiers médicaux. Un importateur OpenAQ optionnel permet de récupérer des mesures environnementales réelles lorsqu'un identifiant de capteur et une clé API sont disponibles. Aucune série hospitalière réelle n'est incluse.

---

## 1. Ce que contient le projet

### A. Le prototype fédéré TP1–TP4 conservé

Le backend initial est conservé :
- API Environment sur le port `8001`.
- API Hospital sur le port `8002`.
- Bases SQLite distinctes dans `data/environment` et `data/hospital`.
- Catalogue de données inspiré de DCAT.
- Contrats dynamiques, finalité, permissions, expiration et révocation.
- Signature HMAC-SHA256 du paquet de classifications.
- Vérification du timestamp et du nonce anti-rejeu.
- Agrégation locale des admissions par classes `HIGH` / `LOW`.
- Seuil minimal de publication de trois jours.
- Budget epsilon persistant par contrat et bruit de Laplace pédagogique.
- Scripts de tests négatifs présents dans `scripts/`.

Les dix jours du support de TP sont conservés dans les bases SQLite d'origine. Ils servent de **jeu de référence pédagogique** : ne pas les remplacer par le jeu étendu.

### B. Extension Data Engineering / Data Science

`data/extended/` contient deux séries quotidiennes synthétiques de 2019 à 2025 :
- `environment/tangier_environment_synthetic.csv` : PM2.5, PM10, NO2, O3, température, humidité, vent, précipitations et indice de trafic.
- `hospital/tangier_hospital_synthetic.csv` : admissions respiratoires quotidiennes et répartitions synthétiques par classes d'âge.

Les données sont reproductibles avec `scripts/generate_demo_data.py` (graine fixe). Elles permettent de tester les pipelines, les graphiques et les modèles sur plusieurs années sans prétendre représenter une population réelle.

### C. Deux expériences Machine Learning locales

`scripts/train_models.py` entraîne et compare, sur une séparation chronologique 80/20 :
1. **Environment — prévision PM2.5** : Random Forest Regressor et HistGradientBoosting Regressor. Les variables utilisent les retards de polluants, moyennes glissantes et variables calendaires/météorologiques.
2. **Hospital — prévision des admissions synthétiques** : Random Forest Regressor et HistGradientBoosting Regressor. Le modèle utilise les retards d'admissions, variables calendaires et une classe de pollution HIGH/LOW plutôt que les mesures environnementales brutes.

Les modèles sont évalués avec MAE, RMSE et R². Le meilleur modèle selon la MAE est sauvegardé dans `models/environment/` et `models/hospital/`. Les prédictions de la période test et les métriques sont exportées dans `frontend/data/dashboard.json`.

**Interprétation scientifique :** les scores du modèle hospitalier ne mesurent pas une performance clinique. Ils mesurent seulement la capacité du modèle à retrouver les motifs du scénario synthétique construit pour cette démonstration. La corrélation affichée est descriptive et ne démontre aucune causalité.

### D. Intelligence Studio (frontend avancé)

Depuis le workspace, ouvrir **AI & Intelligence Studio** ou aller directement à `http://127.0.0.1:5500/advanced.html`.

Cette page présente :
- indicateurs de couverture et de provenance ;
- courbes mensuelles PM2.5, PM10, NO2 et O3 ;
- série mensuelle des admissions ;
- corrélation descriptive et nuage de points ;
- courbes réel / prédit sur la période de test ;
- comparaison MAE, RMSE et R² des deux modèles ;
- schéma de pipeline et de séparation des organisations ;
- indicateurs de qualité et traçabilité.

Les résultats du studio sont pré-calculés par le script ML puis servis par l'API locale Intelligence. Ils ne sont pas calculés à chaque ouverture du navigateur.

---

## 2. Architecture et ports

```text
                    ┌────────────────────────────┐
                    │     University Lab         │
                    │ catalogue / contrats       │
                    │ orchestration / dashboard  │
                    └──────────────┬─────────────┘
                                   │
                         paquet signé / demande
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
┌─────────────▼────────────┐              ┌─────────────▼────────────┐
│ Environment Node : 8001  │              │ Hospital Node : 8002    │
│ SQLite environnement    │              │ SQLite admissions       │
│ classifications signées │─────────────►│ HMAC + nonce + timestamp│
│ catalogue et contrats   │              │ agrégation locale       │
│ ML PM2.5 local (studio) │              │ ML admissions local     │
└─────────────────────────┘              └──────────────────────────┘

Frontend : http://127.0.0.1:5500
Intelligence API : http://127.0.0.1:8003
```

Le service Intelligence (`backend/intelligence_api.py`) sert les artefacts agrégés d'évaluation du studio. C'est un service local de lecture ; il ne remplace pas les nœuds fédérés et ne constitue pas un moteur de fédération de poids ML.

**Ce qui est fédéré dans le prototype actuel :** échange de classifications signées et agrégation autorisée côté Hospital.  
**Ce qui n'est pas implémenté :** entraînement distribué avec agrégation de poids (FedAvg ou équivalent). Ne pas appeler les deux expériences locales « Federated Learning ».

---

## 3. Installation Windows 11

Ouvrir PowerShell dans le dossier racine `FederAir-Health`.

### 3.1 Créer l'environnement Python

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloque l'activation :
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3.2 Configurer les clés

Copier `.env.example` vers `.env`, puis remplacer les valeurs par tes clés locales. Ne jamais publier `.env` sur GitHub.

Le backend initial lit les variables d'environnement. Pour le lancement local, définir les variables dans le terminal avant de démarrer les API, ou utiliser le mécanisme de chargement `.env` déjà présent dans ton environnement si configuré.

Variables :
- `ENVIRONMENT_API_KEY`
- `HOSPITAL_API_KEY`
- `FEDERATION_SECRET`
- `OPENAQ_API_KEY` (optionnelle, uniquement pour l'import réel)

### 3.3 Générer le jeu de démonstration et entraîner les modèles

```powershell
python -m scripts.generate_demo_data
python -m scripts.train_models
```

Le second script crée :
- `models/environment/pm25_forecaster.joblib`
- `models/hospital/admissions_forecaster.joblib`
- `models/training_report.json`
- `frontend/data/dashboard.json`

Les modèles sont entraînés sur CPU et conçus pour rester légers sur un PC avec 8 Go de RAM.

---

## 4. Lancer les quatre services

Ouvrir quatre terminaux PowerShell distincts, tous depuis la racine du projet et avec `.venv` activé.

**Terminal 1 — Environment**
```powershell
python -m uvicorn backend.node_environment.api:app --host 127.0.0.1 --port 8001
```
Swagger : http://127.0.0.1:8001/docs

**Terminal 2 — Hospital**
```powershell
python -m uvicorn backend.node_hospital.api:app --host 127.0.0.1 --port 8002
```
Swagger : http://127.0.0.1:8002/docs

**Terminal 3 — Intelligence API**
```powershell
python -m uvicorn backend.intelligence_api:app --host 127.0.0.1 --port 8003
```
Swagger : http://127.0.0.1:8003/docs

**Terminal 4 — Frontend**
```powershell
cd frontend
node server.mjs
```
Ouvrir : http://127.0.0.1:5500

Configurer les deux clés API dans « Configuration des connexions » du workspace. Les clés sont conservées dans `sessionStorage` pour la session du navigateur.

---

## 5. Importer des observations environnementales réelles (optionnel)

OpenAQ v3 expose des mesures publiques, y compris PM2.5, PM10, NO2, O3, température et humidité pour les stations qui disposent de ces paramètres. La couverture n'est pas uniforme : il faut vérifier les capteurs disponibles à Tanger et leur période avant de conclure qu'une série est suffisante.

Documentation :
- OpenAQ API : https://api.openaq.org/docs
- Guide mesures : https://docs.openaq.org/resources/measurements

Étapes :
1. Créer/obtenir une clé API OpenAQ.
2. Identifier un capteur PM2.5 de la zone de Tanger dans la documentation / API OpenAQ.
3. Définir la clé dans PowerShell :
```powershell
$env:OPENAQ_API_KEY="TA_CLE_OPENAQ"
```
4. Importer le capteur (remplacer `SENSOR_ID`) :
```powershell
python -m scripts.import_openaq_pm25 --sensor-id SENSOR_ID --date-from 2020-01-01 --date-to 2025-12-31
```
5. Le fichier est écrit dans :
`data/extended/environment/tangier_openaq_pm25.csv`

### Alternative : estimations PM2.5 de la Banque mondiale

La Banque mondiale publie un fichier régional MENA couvrant notamment les villes de la région, période 2018–2026 (archive régionale d'environ 75,5 MB au moment de la consultation). Télécharger l'archive depuis la fiche officielle, l'extraire, puis inspecter les noms de colonnes du CSV.

Fiche officielle : https://datacatalog.worldbank.org/search/dataset/0067162/daily-city-level-air-pollution-pm2-5-estimates-2018-2026

Normaliser ensuite le fichier en indiquant les noms exacts de colonnes :
```powershell
python -m scripts.prepare_worldbank_pm25 --input "CHEMIN\VERS\FICHIER.csv" --date-column "DATE_COL" --city-column "CITY_COL" --value-column "PM25_COL" --city "Tangier"
```
Le résultat est une estimation quotidienne PM2.5 à l'échelle de la ville produite par un modèle global, pas une mesure directe de station. Vérifier le nom de ville présent dans l'archive.

Pour entraîner sur ce CSV au lieu de l'environnement synthétique :
```powershell
$env:FEDERAIR_ENVIRONMENT_CSV="data/extended/environment/tangier_openaq_pm25.csv"
python -m scripts.train_models
```

L'importeur ne fabrique pas de mesures PM10/NO2/O3 ou météo manquantes. Les variables absentes sont imputées par le pipeline ML et le résultat doit être interprété avec prudence. Vérifier le capteur, la localisation, les unités, les licences et les trous de mesure. Le jeu hospitalier reste synthétique.

---

## 6. Explication des mécanismes backend existants

### Catalogue
Le nœud Environment publie des métadonnées : identifiant, titre, description, éditeur, couverture temporelle, unité, finalités et point d'accès. Le catalogue est inspiré de DCAT, sans prétendre implémenter l'intégralité du standard.

### Contrats
Le laboratoire demande un contrat avec dataset, consommateur, finalité, permissions et durée. Environment valide la demande et conserve le contrat. Un contrat peut être consulté ou révoqué.

### HMAC-SHA256
Environment signe le paquet de classifications. Hospital recalcule la signature avec le secret partagé et compare les empreintes. HMAC protège l'intégrité et l'authenticité du paquet ; **il ne chiffre pas les données**.

### Anti-rejeu
Un timestamp limite l'âge du paquet et un nonce unique est enregistré dans SQLite. Une seconde transmission du même nonce est rejetée.

### Agrégation locale
Hospital associe les classifications aux admissions de sa propre base, forme les groupes HIGH et LOW et calcule les agrégats localement. Le laboratoire ne reçoit que les résultats autorisés.

### Seuil minimal
Un groupe de moins de trois jours n'est pas publié. Ce seuil est une règle de minimisation pédagogique ; il ne constitue pas une preuve de k-anonymat.

### Bruit de Laplace et budget epsilon
Le prototype applique un bruit de Laplace et suit un budget epsilon persistant par contrat. Le support TP précise que le mécanisme est pédagogique et ne constitue pas une garantie formelle complète de confidentialité différentielle. Le budget doit être réévalué si de nouvelles statistiques ou prédictions sont publiées.

---

## 7. Tests du prototype fédéré

Depuis la racine, avec les deux API démarrées :

```powershell
python -m scripts.test_rest_communication
python -m scripts.test_hmac_tampering
python -m scripts.test_replay_attack
python -m scripts.test_privacy_budget
python -m backend.tests.test_contracts
python -m backend.tests.test_contract_persistence
```

Attention : `test_privacy_budget.py` et `test_replay_attack.py` peuvent consommer du budget ou enregistrer des nonces. Utiliser des contrats de test dédiés. Ne pas lancer les scripts plusieurs fois avec le même contrat de démonstration sans vérifier son budget.

---

## 8. Structure du projet

```text
FederAir-Health/
├── backend/
│   ├── common/                  # configuration et sécurité partagées
│   ├── node_environment/        # nœud propriétaire Environment
│   ├── node_hospital/           # nœud propriétaire Hospital
│   └── intelligence_api.py      # API locale des résultats ML
├── data/
│   ├── environment/             # SQLite TP d'origine
│   ├── hospital/                # SQLite TP d'origine
│   └── extended/                # CSV démonstration étendus
├── models/
│   ├── environment/             # modèle PM2.5 sauvegardé
│   ├── hospital/                # modèle admissions sauvegardé
│   └── training_report.json
├── frontend/
│   ├── index.html               # workspace fédéré
│   ├── advanced.html            # Intelligence Studio
│   ├── advanced.js / advanced.css
│   ├── data/dashboard.json      # agrégats et résultats ML
│   └── server.mjs               # serveur statique + proxy API
├── scripts/
│   ├── generate_demo_data.py
│   ├── import_openaq_pm25.py
│   ├── train_models.py
│   └── tests existants
├── .env.example
├── requirements.txt
└── README.md
```

---

## 9. Limites et transparence scientifique

1. Les séries étendues livrées sont synthétiques et doivent être présentées comme telles.
2. L'import OpenAQ réel est optionnel et nécessite une clé API ainsi qu'un identifiant de capteur vérifié.
3. Aucune donnée hospitalière réelle n'est fournie.
4. Les métriques ML du ZIP décrivent un scénario synthétique ; elles ne prouvent pas une performance opérationnelle ou médicale.
5. Une corrélation ne démontre pas une causalité.
6. Les résultats de bruit de Laplace sont pédagogiques et ne doivent pas être annoncés comme une garantie formelle de differential privacy.
7. Le dashboard AI Studio lit des résultats pré-calculés par `train_models.py`. L'API Intelligence ne récupère pas les données brutes des deux organisations.
8. Le projet ne met pas en œuvre de Federated Learning par agrégation de poids de modèles.

---

## 10. Sources de données et références

- OpenAQ API v3 : https://api.openaq.org/docs
- OpenAQ — Measurements : https://docs.openaq.org/resources/measurements
- World Bank — Daily City-Level Air Pollution PM2.5 Estimates, 2018–2026 : https://datacatalog.worldbank.org/search/dataset/0067162/daily-city-level-air-pollution-pm2-5-estimates-2018-2026
- Copernicus ERA5 hourly single levels : https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
- Copernicus ERA5 hourly time-series : https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries

Pour les jeux de données tiers, conserver la citation, la licence, l'identifiant de station/capteur, la date de récupération et la version du fichier dans tout rapport final.

---

**FederAir Health — Un prototype de recherche fédérée, enrichi par des expériences reproductibles de Data Engineering et de Machine Learning.**
