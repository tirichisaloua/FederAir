
import os
from pathlib import Path
from dotenv import load_dotenv

# Racine du projet FederAir-Health
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

# Dossiers de stockage propres à chaque organisation
DATA_DIR = PROJECT_ROOT / "data"

ENVIRONMENT_DIR = DATA_DIR / "environment"
HOSPITAL_DIR = DATA_DIR / "hospital"

ENVIRONMENT_DB = ENVIRONMENT_DIR / "environment.db"
HOSPITAL_DB = HOSPITAL_DIR / "hospital.db"

# Identifiants des organisations
ENVIRONMENT_API_KEY = os.getenv(
    "ENVIRONMENT_API_KEY", "dev-environment-key"
)

HOSPITAL_API_KEY = os.getenv(
    "HOSPITAL_API_KEY", "dev-hospital-key"
)

FEDERATION_SECRET = os.getenv(
    "FEDERATION_SECRET", "dev-federation-secret"
)

# Paramètres métier
PM25_THRESHOLD = 30.0
MIN_GROUP_SIZE = 3
MAX_DAILY_ADMISSIONS = 30.0
MAX_EPSILON_BUDGET = 3.0

def create_directories():
    """Crée les dossiers nécessaires au stockage local."""
    ENVIRONMENT_DIR.mkdir(parents=True, exist_ok=True)
    HOSPITAL_DIR.mkdir(parents=True, exist_ok=True)

# Identité du partage fédéré
FEDERATION_CONTRACT_ID = "CONTRACT-FEDERAIR-001"
FEDERATION_CONSUMER_ID = "UNIVERSITY-LAB"