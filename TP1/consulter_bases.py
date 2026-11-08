"""TP1 - Consultation du contenu des deux bases."""
import sqlite3
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
requetes = [
    ("environnement.db", "SELECT * FROM qualite_air ORDER BY date"),
    ("hopital.db", "SELECT * FROM admissions ORDER BY date"),
]

for fichier, requete in requetes:
    print("\nBase :", fichier)
    db = sqlite3.connect(DOSSIER / fichier)
    for ligne in db.execute(requete):
        print(ligne)
    db.close()
