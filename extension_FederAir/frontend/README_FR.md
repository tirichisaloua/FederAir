# Frontend FederAir Health

Le workspace principal est `index.html`. Le studio analytique est `advanced.html`.

Le serveur `server.mjs` sert les fichiers statiques et relaie les requêtes vers Environment (8001), Hospital (8002) et Intelligence API (8003).

Lancer depuis ce dossier : `node server.mjs`, puis ouvrir http://127.0.0.1:5500.

Pour afficher les résultats ML, exécuter au préalable depuis la racine : `python -m scripts.train_models`. Les graphiques du studio lisent les agrégats pré-calculés depuis l'API Intelligence.
