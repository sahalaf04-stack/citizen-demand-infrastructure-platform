# Citizen Demand & Infrastructure Priority Platform — MVP scaffold

A working demo slice of the full architecture: citizen requests in, multilingual
NLP extraction, deduplication into demand hotspots, transparent priority
scoring, and a policymaker dashboard with a map.

Runs entirely offline with synthetic demo data — no API keys required to see
it working end to end.

## What's real vs. stubbed

| Piece | This scaffold | Production swap |
|---|---|---|
| Translation/NLU | Keyword-based fallback (works offline), or Claude API if `ANTHROPIC_API_KEY` is set | Bhashini API for ASR + translation |
| Intake channel | Direct API + synthetic seed data | WhatsApp Business API / IVR adapter calling the same `/api/requests` endpoint |
| Database | SQLite | Postgres + PostGIS |
| Dedup | TF-IDF cosine similarity | Embedding similarity + FAISS at national scale |
| Demographic/infra data | Real: 6 official NITI Aayog "Aspirational Districts" + real 2011 Census populations. Illustrative: infra_deficit_score and planned_budget_cr (not sourced) | Pull live from championsofchange.gov.in delta rankings + real scheme budget data |

## 1. Open in VS Code

Open the `citizen-platform` folder in VS Code. Install the **Python** and
**ES7+ React** extensions if prompted — not required, just convenient.

## 2. Run the backend

Open a VS Code terminal (`` Ctrl+` ``):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py             # populates 6 districts + ~180 synthetic requests
uvicorn main:app --reload --port 8000
```

Leave this running. API docs are auto-generated at `http://localhost:8000/docs`
— useful for poking at `/api/hotspots` and `/api/priorities` directly.

## 3. Run the frontend

Open a **second** terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. You should see the map populate with demand
hotspots and the ranked priority list on the right.

If the dashboard looks empty, click **seed demo data** in the sidebar — it
calls `POST /api/seed` and refreshes.

## 4. Optional: enable real LLM extraction

By default the NLP pipeline uses a keyword-based classifier so it runs with
zero setup. To use Claude for translation + classification instead:

```powershell
cd backend
copy .env.example .env
```

Open `.env` in VS Code and paste in your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Get a key at https://console.anthropic.com/settings/keys if you don't have
one. Restart `uvicorn` (`Ctrl+C` then re-run `uvicorn main:app --reload --port 8000`)
so it picks up the `.env` file, then re-run `python seed_data.py` to
regenerate the demo requests with real translation instead of the keyword
fallback.

`nlp_pipeline.py` automatically switches to `_llm_extract()` whenever
`ANTHROPIC_API_KEY` is set — no other code changes needed. If the API call
ever fails (rate limit, network issue), it silently falls back to the
keyword classifier rather than breaking intake.

**Do not commit `.env`** — it's already excluded via `.gitignore`, since it
will contain your real API key.

## About the district data

The 6 districts in `seed_data.py` are real, not made up: Raichur, Nandurbar,
Purnia, Wayanad, Chamba, and Dahod are all on NITI Aayog's official list of
112 "Aspirational Districts" — a real government designation for
under-developed districts prioritized for accelerated development since
2018. Their populations are real 2011 Census figures.

What's *not* sourced yet: `infra_deficit_score` and `planned_budget_cr` are
illustrative placeholders. NITI Aayog does publish a real monthly composite
score for these districts via the Champions of Change dashboard
(championsofchange.gov.in) — swapping the placeholder score for that real
figure is the natural next step and would make the priority ranking fully
defensible end to end.

## 5. Where to extend next

- **Add a real intake channel**: point a WhatsApp webhook or IVR callback at
  `POST /api/requests` — the payload shape is already defined in `main.py`.
- **Swap in Bhashini**: replace the translation step inside
  `nlp_pipeline.py` with a call to Bhashini's ASR/translation APIs.
- **Real district data**: replace the `DISTRICTS` list in `seed_data.py`
  with a loader that reads from an actual SDG India Index / census export.
- **Adjust priority weights**: the scoring formula weights live at the top
  of `scoring.py` — make them configurable per state if states weight
  demand vs. infra-deficit differently.

## Project structure

```
citizen-platform/
├── backend/
│   ├── main.py            # FastAPI app + endpoints
│   ├── models.py          # SQLAlchemy models (CitizenRequest, District)
│   ├── database.py        # DB session setup (SQLite -> swap for Postgres)
│   ├── nlp_pipeline.py     # translation + intent/urgency extraction
│   ├── dedup.py            # near-duplicate clustering + hotspot aggregation
│   ├── scoring.py          # transparent priority scoring formula
│   ├── seed_data.py        # synthetic demo data generator
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── index.css
    │   └── components/
    │       ├── HotspotMap.jsx
    │       └── PriorityList.jsx
    └── package.json
```
