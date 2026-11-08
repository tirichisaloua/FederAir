"""Read-only API for precomputed local ML experiment outputs."""
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "frontend" / "data" / "dashboard.json"
app = FastAPI(title="FederAir Intelligence API", version="1.0.0",
              description="Serves aggregated dashboard and model evaluation artifacts.")

@app.get("/health")
def health():
    return {"service":"FederAir Intelligence API","status":"ok"}

@app.get("/api/v1/dashboard")
def dashboard():
    if not DASHBOARD.exists():
        raise HTTPException(status_code=503, detail="Dashboard artifact missing. Run scripts/train_models.py.")
    return json.loads(DASHBOARD.read_text(encoding="utf-8"))
