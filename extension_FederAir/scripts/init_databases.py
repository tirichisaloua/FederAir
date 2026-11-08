import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.node_environment.database import (
    init_database as init_environment
)

from backend.node_hospital.database import (
    init_database as init_hospital
)


def main():
    print("=" * 50)
    print("       FEDERAIR HEALTH - DATABASE SETUP")
    print("=" * 50)

    print("\n[1/2] Initializing Environment node...")
    init_environment()

    print("\n[2/2] Initializing Hospital node...")
    init_hospital()

    print("\nDatabase initialization completed successfully.")


if __name__ == "__main__":
    main()
