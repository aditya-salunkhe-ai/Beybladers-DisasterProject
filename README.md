# Beybladers MVP — Checkpoint G (Deployment Ready)

Functional screening MVP for priority-aware disaster resource allocation.

## Implemented demo lifecycle
Emergency intake → START triage/priority → constraint-aware candidate evaluation → explainable allocation → human-confirmed dispatch → live disruption simulation → automatic re-optimization/re-allocation → delivery confirmation → timestamped audit trace.

All operational data and disruption controls are explicitly simulated prototype data.

## Local run
### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL (normally `http://localhost:5173`).

## Deployment
See `DEPLOYMENT.md`. A Render blueprint (`render.yaml`), backend Dockerfile, Vercel SPA config, `.env.example`, health endpoint, and automatic first-start demo seeding are included.

## Proposed architecture vs prototype
The screening MVP intentionally uses FastAPI + SQLite + React/Vite to demonstrate the end-to-end decision loop quickly. PostgreSQL/PostGIS, Redis, OR-Tools/advanced optimization, OSRM/live routing, Hyperledger Fabric, production authentication and real agency feeds remain proposed production architecture unless separately implemented.

## Checkpoint H hardening
- Refresh-safe hash navigation: each page has a stable `#command`, `#requests`, `#allocation`, `#operations`, or `#audit` URL.
- Responsive alignment fixes for tables, headers, live operations and smaller screens.
- Safe handling when no feasible allocation exists.
- Added relief resource types so Medicine/Food/Water/Medical Team requests can be evaluated.
- General-bed capacity matching corrected.
- Added `POST /api/demo/reset` and a Command Center **Reset Demo** control for repeatable judging runs.
- SQLAlchemy requirement accepts the installed Python 3.13-compatible 2.1.x line.

## Final QA polish
- Refresh controls on Command Center, Emergency Requests, Live Operations and Tracking & Audit now visibly re-fetch data and show the last update time.
- Tracking & Audit timeline styles are isolated from the Command Center activity feed to prevent clipping/alignment conflicts.
- Decision Logic / Dynamic Loop is styled as an explanatory process strip rather than an input-like dark bar.
