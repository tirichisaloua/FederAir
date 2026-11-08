"""TP2 - API de l'organisation B (hôpital). Données brutes exposées."""
import sqlite3
from pathlib import Path
from fastapi import FastAPI

DB = Path(__file__).resolve().parent / "hopital.db"
app = FastAPI(title="API Hôpital")


@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}


@app.get("/admissions")
def obtenir_admissions():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    lignes = db.execute("""
        SELECT date, ville, nombre
        FROM admissions ORDER BY date
    """).fetchall()
    db.close()
    return [dict(ligne) for ligne in lignes]


@app.get("/statistiques")
def statistiques():
    db = sqlite3.connect(DB)
    resultat = db.execute("SELECT COUNT(*), AVG(nombre) FROM admissions").fetchone()
    db.close()
    return {"nombre_jours": resultat[0], "moyenne_admissions": round(resultat[1], 2)}
