# Beybladers MVP — Deployment Checklist

## 1) Deploy backend (Render)
1. Push this project to GitHub.
2. In Render create a **Web Service** from the repository.
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Health check: `/health`
7. After deployment, open `https://<your-render-url>/health` and confirm `{"status":"ok",...}`.

The demo database auto-seeds on first startup when empty. The hosted SQLite database is suitable for this screening demo, not for production persistence/scaling.

## 2) Deploy frontend (Vercel)
1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework preset: Vite.
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add environment variable:
   `VITE_API_URL=https://<your-render-backend-url>`
7. Deploy.

## 3) Judge test
Open the public frontend URL in an incognito/private window and run this exact flow:
1. Emergency Requests → create RED medical request requiring Ambulance + ICU.
2. Resource Allocation → evaluate candidates → confirm recommendation → dispatch.
3. Live Operations → mark En Route.
4. Simulate ICU full or route block → verify automatic re-allocation.
5. Confirm Delivery / Admission.
6. Audit & Tracking → show the complete timestamped trace.

## 4) Prototype slide evidence
Capture four real screenshots from the deployed app:
- Command Center
- Intelligent Allocation + “Why this allocation?”
- Re-optimized allocation after disruption (hero screenshot)
- Audit & Tracking after delivery

Place a QR code to the **public frontend URL** on the Prototype & Validation slide. Also show a short readable URL. If a demo video is made, add it as a secondary link/QR only.

## 5) Before PPT/PDF submission
- Test QR from a phone.
- Test public URL while logged out.
- Test the full scenario from a fresh/reset demo state.
- Export PDF and verify QR still scans.
- Do not claim live government feeds, production GPS, blockchain verification, or production-grade persistence unless actually implemented.
