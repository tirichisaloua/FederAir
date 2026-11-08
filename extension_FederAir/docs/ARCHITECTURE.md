# Architecture technique

## Nœuds
- Environment : FastAPI, SQLite, catalogue, contrats, classifications signées.
- Hospital : FastAPI, SQLite, vérification HMAC, anti-rejeu, agrégation et budget de confidentialité.
- University Lab : client orchestrateur dans le navigateur ; il demande un contrat, récupère un paquet signé et transmet le paquet à Hospital.
- Intelligence API : service local read-only qui sert les métriques et séries agrégées pré-calculées par les scripts ML.

## Flux du TP
1. Le laboratoire découvre les métadonnées du dataset.
2. Il demande un contrat avec finalité et permissions.
3. Environment vérifie le contrat et signe les classifications.
4. Le laboratoire relaie le paquet sans modifier son contenu.
5. Hospital vérifie la clé API, l'identité du consommateur, l'intégrité HMAC, la fraîcheur du timestamp et l'unicité du nonce.
6. Hospital associe les catégories aux admissions de sa base locale, applique le seuil et le bruit pédagogique, puis renvoie uniquement les agrégats.
7. Le laboratoire affiche les résultats.

## Extension analytique
Les scripts génèrent un jeu de démonstration, entraînent deux modèles CPU locaux et écrivent des résultats de test agrégés dans `frontend/data/dashboard.json`. L'Intelligence API lit ce fichier et le sert au studio analytique.

Cette extension ne constitue pas un protocole de Federated Learning : il n'y a pas d'échange ni d'agrégation de poids de modèles entre nœuds. Elle illustre deux expériences de ML séparées, rattachées à des domaines de données distincts.
