from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from a .env file if present

from database import engine, Base, get_db
from models import CitizenRequest, District
from nlp_pipeline import process_request
from dedup import assign_clusters, compute_hotspots
from scoring import rank_districts
from seed_data import seed

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Citizen Demand Aggregation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://citizen-demand-infrastructure-platf.vercel.app",
],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestIn(BaseModel):
    text: str
    language: str = "en"
    lat: float
    lon: float
    district_id: int


@app.post("/api/seed")
def api_seed():
    """Convenience endpoint to (re)populate demo data. Do not expose in production."""
    seed()
    return {"status": "seeded"}


@app.post("/api/requests")
def submit_request(payload: RequestIn, db: Session = Depends(get_db)):
    """Citizen intake endpoint - this is what your WhatsApp/IVR/web adapters call."""
    extracted = process_request(payload.text, payload.language)
    req = CitizenRequest(
        raw_text=payload.text,
        language=payload.language,
        translated_text=extracted["translated_text"],
        category=extracted["category"],
        urgency=extracted["urgency"],
        lat=payload.lat,
        lon=payload.lon,
        district_id=payload.district_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"id": req.id, "category": req.category, "urgency": req.urgency}


def _load_requests_with_district(db: Session):
    rows = (
        db.query(CitizenRequest, District)
        .join(District, CitizenRequest.district_id == District.id)
        .all()
    )
    return [
        {
            "id": r.id,
            "district_id": r.district_id,
            "district_name": d.name,
            "category": r.category,
            "urgency": r.urgency,
            "translated_text": r.translated_text,
            "lat": r.lat,
            "lon": r.lon,
        }
        for r, d in rows
    ]


@app.get("/api/requests")
def list_requests(db: Session = Depends(get_db)):
    return _load_requests_with_district(db)


@app.get("/api/hotspots")
def get_hotspots(db: Session = Depends(get_db)):
    """Dedup requests into distinct-issue clusters, then aggregate per district."""
    requests = _load_requests_with_district(db)
    cluster_map = assign_clusters(requests)
    for r in requests:
        r["cluster_id"] = cluster_map[r["id"]]
    return compute_hotspots(requests)


@app.get("/api/priorities")
def get_priorities(db: Session = Depends(get_db)):
    """The main policymaker-facing endpoint: ranked, explainable project list."""
    requests = _load_requests_with_district(db)
    cluster_map = assign_clusters(requests)
    for r in requests:
        r["cluster_id"] = cluster_map[r["id"]]
    hotspots = compute_hotspots(requests)

    districts = db.query(District).all()
    districts_by_id = {
        d.id: {
            "infra_deficit_score": d.infra_deficit_score,
            "population": d.population,
            "planned_budget_cr": d.planned_budget_cr,
            "state": d.state,
            "name": d.name,
        }
        for d in districts
    }
    return rank_districts(hotspots, districts_by_id)


@app.get("/api/districts")
def list_districts(db: Session = Depends(get_db)):
    return db.query(District).all()
