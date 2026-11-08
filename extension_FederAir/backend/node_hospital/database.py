
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from backend.common.config import HOSPITAL_DB, create_directories, MAX_EPSILON_BUDGET


# Données fictives du TP 4
HOSPITAL_DATA = [
    ("2026-10-01", "Tanger", 8),
    ("2026-10-02", "Tanger", 14),
    ("2026-10-03", "Tanger", 18),
    ("2026-10-04", "Tanger", 9),
    ("2026-10-05", "Tanger", 16),
    ("2026-10-06", "Tanger", 20),
    ("2026-10-07", "Tanger", 10),
    ("2026-10-08", "Tanger", 7),
    ("2026-10-09", "Tanger", 13),
    ("2026-10-10", "Tanger", 5),
]


def init_database():
    """Initialise la base locale de l'organisation Hôpital."""

    create_directories()

    with closing(sqlite3.connect(HOSPITAL_DB)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admissions (
                    date TEXT PRIMARY KEY,
                    city TEXT NOT NULL,
                    number_of_admissions INTEGER NOT NULL
                        CHECK(number_of_admissions >= 0)
                )
            """)

            conn.executemany("""
                INSERT OR IGNORE INTO admissions
                    (date, city, number_of_admissions)
                VALUES (?, ?, ?)
            """, HOSPITAL_DATA)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS used_nonces (
                    nonce TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS privacy_budget (
                    contract_id TEXT PRIMARY KEY,
                    epsilon_spent REAL NOT NULL DEFAULT 0.0
                        CHECK(epsilon_spent >= 0),
                    updated_at TEXT NOT NULL
                )
            """)

    print(f"[HOSPITAL] Database ready: {HOSPITAL_DB}")


def get_all_admissions():
    """Retourne les admissions depuis la base locale."""

    with closing(sqlite3.connect(HOSPITAL_DB)) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT date, city, number_of_admissions
            FROM admissions
            ORDER BY date
        """).fetchall()

        return [dict(row) for row in rows]


def get_admissions_by_date():
    """Retourne les admissions sous forme de dictionnaire."""

    with closing(sqlite3.connect(HOSPITAL_DB)) as conn:
        rows = conn.execute("""
            SELECT date, number_of_admissions
            FROM admissions
        """).fetchall()

        return {date: number for date, number in rows}



def register_nonce(nonce: str, timestamp: int) -> bool:
    """
    Enregistre un nonce utilisé.

    Retourne True si le nonce est nouveau.
    Retourne False s'il existe déjà.
    """

    with closing(sqlite3.connect(HOSPITAL_DB)) as conn:
        try:
            with conn:
                conn.execute("""
                    INSERT INTO used_nonces (nonce, timestamp)
                    VALUES (?, ?)
                """, (nonce, timestamp))

            return True

        except sqlite3.IntegrityError:
            return False

def consume_privacy_budget(contract_id: str, epsilon: float) -> bool:
    """
    Consomme le budget de confidentialité d'un contrat.
    L'opération est protégée par une transaction SQLite.
    """

    if epsilon <= 0 or epsilon > MAX_EPSILON_BUDGET:
        return False

    with closing(sqlite3.connect(HOSPITAL_DB, timeout=10)) as conn:
        try:
            # Réserver l'accès en écriture avant de lire le budget.
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute("""
                SELECT epsilon_spent
                FROM privacy_budget
                WHERE contract_id = ?
            """, (contract_id,)).fetchone()

            current_spent = row[0] if row else 0.0
            new_total = current_spent + epsilon

            if new_total > MAX_EPSILON_BUDGET:
                conn.rollback()
                return False

            now = datetime.now(timezone.utc).isoformat()

            conn.execute("""
                INSERT INTO privacy_budget (
                    contract_id,
                    epsilon_spent,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(contract_id)
                DO UPDATE SET
                    epsilon_spent = excluded.epsilon_spent,
                    updated_at = excluded.updated_at
            """, (contract_id, new_total, now))

            conn.commit()
            return True

        except sqlite3.Error:
            conn.rollback()
            raise