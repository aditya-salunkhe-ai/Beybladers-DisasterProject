from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import EmergencyRequest, Resource, Allocation, Route
router=APIRouter(prefix="/api",tags=["dashboard"])
@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db)):
    return {
      "active_requests": db.query(EmergencyRequest).filter(EmergencyRequest.status.notin_(["DELIVERED","CLOSED","CANCELLED"])).count(),
      "critical_requests": db.query(EmergencyRequest).filter(EmergencyRequest.triage_category=="RED").count(),
      "available_resources": db.query(Resource).filter(Resource.status=="AVAILABLE").count(),
      "active_dispatches": db.query(Allocation).filter(Allocation.status.in_(["ACTIVE","DISPATCHED","EN_ROUTE"])).count(),
      "active_disruptions": db.query(Route).filter((Route.is_available==False)|(Route.condition=="BLOCKED")).count()
    }
