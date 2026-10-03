from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base,engine,SessionLocal
from routers import dashboard,requests,catalog,allocations,operations
from models import EmergencyRequest
from seed import seed
Base.metadata.create_all(bind=engine)
app=FastAPI(title="Beybladers Disaster Response API",version="0.1.0",description="Simulated disaster-response MVP for priority-aware resource allocation.")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(dashboard.router); app.include_router(requests.router); app.include_router(catalog.router); app.include_router(allocations.router); app.include_router(operations.router)

@app.on_event("startup")
def ensure_demo_data():
    db=SessionLocal()
    try:
        count=db.query(EmergencyRequest).count()
    finally:
        db.close()
    if count==0:
        seed()

@app.get("/health")
def health():
    return {"status":"ok","service":"beybladers-api"}

@app.get("/")
def root(): return {"name":"Beybladers Disaster Response API","status":"operational","environment":"SIMULATED DEMO"}

@app.post("/api/demo/reset")
def reset_demo():
    """Restore the deterministic simulated dataset for repeatable judging/demo runs."""
    seed()
    return {"status":"reset","message":"Demo state restored"}
