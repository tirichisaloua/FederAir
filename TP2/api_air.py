"""TP2 - API de l'organisation A (environnement). Données brutes exposées."""
import sqlite3
from pathlib import Path
from fastapi import FastAPI

DB = Path(__file__).resolve().parent / "environnement.db"
app = FastAPI(title="API Environnement")


@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement"}


@app.get("/mesures")
def obtenir_mesures():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    lignes = db.execute("""
        SELECT date, ville, pm25
        FROM qualite_air ORDER BY date
    """).fetchall()
    db.close()
    return [dict(ligne) for ligne in lignes]


@app.get("/statistiques")
def statistiques():
    db = sqlite3.connect(DB)
    resultat = db.execute("SELECT COUNT(*), AVG(pm25) FROM qualite_air").fetchone()
    db.close()
    return {"nombre_jours": resultat[0], "moyenne_pm25": round(resultat[1], 2)}
