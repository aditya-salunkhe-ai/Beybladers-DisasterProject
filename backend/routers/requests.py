from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import EmergencyRequest, SystemEvent
from schemas import RequestCreate
from services.priority_engine import calculate_priority
from datetime import datetime
router=APIRouter(prefix="/api/requests",tags=["requests"])
@router.get("")
def list_requests(db:Session=Depends(get_db)):
    return db.query(EmergencyRequest).order_by(EmergencyRequest.priority_score.desc()).all()
@router.post("")
def create_request(data:RequestCreate,db:Session=Depends(get_db)):
    n=db.query(EmergencyRequest).count()+105
    rid=f"REQ-{n:03}"; score=calculate_priority(data.triage_category,data.waiting_minutes)
    req=EmergencyRequest(request_id=rid,**data.model_dump(),priority_score=score,status="PRIORITIZED")
    db.add(req); db.add(SystemEvent(event_id=f"EVT-{int(datetime.utcnow().timestamp()*1000)}",event_type="REQUEST_CREATED",request_id=rid,actor="Command Center",message=f"{rid} received and prioritized as {data.triage_category.upper()} • Score {score}")); db.commit(); db.refresh(req); return req
