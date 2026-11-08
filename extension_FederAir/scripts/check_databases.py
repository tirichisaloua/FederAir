import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.node_environment.database import get_all_measurements
from backend.node_hospital.database import get_all_admissions

air = get_all_measurements()
hospital = get_all_admissions()

print("\nENVIRONMENT DATA")
print("-" * 45)

for row in air:
    print(row)

print("\nHOSPITAL DATA")
print("-" * 45)

for row in hospital:
    print(row)

print("\nINTEGRITY CHECK")
print("-" * 45)

print("Environment records:", len(air))
print("Hospital records:", len(hospital))

assert len(air) == 10
assert len(hospital) == 10

assert air[0]["date"] == hospital[0]["date"]
assert air[-1]["date"] == hospital[-1]["date"]

print("\nAll database checks passed!")
