
import sqlite3
from contextlib import closing
import json

from backend.common.config import ENVIRONMENT_DB, create_directories


# Données fictives du TP 4
AIR_DATA = [
    ("2026-10-01", "Tanger", 12.0),
    ("2026-10-02", "Tanger", 35.5),
    ("2026-10-03", "Tanger", 42.1),
    ("2026-10-04", "Tanger", 15.2),
    ("2026-10-05", "Tanger", 38.0),
    ("2026-10-06", "Tanger", 45.0),
    ("2026-10-07", "Tanger", 22.1),
    ("2026-10-08", "Tanger", 18.0),
    ("2026-10-09", "Tanger", 31.0),
    ("2026-10-10", "Tanger", 11.5),
]



def init_database():
    """Initialise la base locale de l'organisation Environnement."""

    create_directories()

    with closing(sqlite3.connect(ENVIRONMENT_DB)) as conn:
        with conn:
            # Table des mesures environnementales
            conn.execute("""
                CREATE TABLE IF NOT EXISTS air_quality (
                    date TEXT PRIMARY KEY,
                    city TEXT NOT NULL,
                    pm25 REAL NOT NULL CHECK(pm25 >= 0)
                )
            """)

            conn.executemany("""
                INSERT OR IGNORE INTO air_quality
                    (date, city, pm25)
                VALUES (?, ?, ?)
            """, AIR_DATA)

            # Table des contrats d'utilisation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    contract_id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    consumer_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK(status IN ('active', 'revoked'))
                )
            """)

    print(f"[ENVIRONMENT] Database ready: {ENVIRONMENT_DB}")



def get_all_measurements():
    """Retourne les mesures locales de qualité de l'air."""

    with closing(sqlite3.connect(ENVIRONMENT_DB)) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT date, city, pm25
            FROM air_quality
            ORDER BY date
        """).fetchall()

        return [dict(row) for row in rows]


def save_contract(contract: dict):
    """Enregistre un contrat dans la base Environment."""

    with closing(sqlite3.connect(ENVIRONMENT_DB)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO contracts (
                    contract_id,
                    dataset_id,
                    consumer_id,
                    purpose,
                    permissions,
                    created_at,
                    expires_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract["contract_id"],
                contract["dataset_id"],
                contract["consumer_id"],
                contract["purpose"],
                json.dumps(contract["permissions"]),
                contract["created_at"],
                contract["expires_at"],
                contract["status"]
            ))


def get_contract(contract_id: str):
    """Récupère un contrat par son identifiant."""

    with closing(sqlite3.connect(ENVIRONMENT_DB)) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT *
            FROM contracts
            WHERE contract_id = ?
        """, (contract_id,)).fetchone()

        if row is None:
            return None

        contract = dict(row)
        contract["permissions"] = json.loads(
            contract["permissions"]
        )

        return contract


def revoke_contract(contract_id: str):
    """Révoque un contrat actif."""

    with closing(sqlite3.connect(ENVIRONMENT_DB)) as conn:
        with conn:
            cursor = conn.execute("""
                UPDATE contracts
                SET status = 'revoked'
                WHERE contract_id = ?
                AND status = 'active'
            """, (contract_id,))

            return cursor.rowcount > 0
