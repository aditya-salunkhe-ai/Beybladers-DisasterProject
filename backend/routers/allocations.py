from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import EmergencyRequest, Allocation, Resource, SystemEvent, Route
from services.allocation_engine import evaluate_candidates

router=APIRouter(prefix='/api',tags=['allocations'])

def event_id(): return f"EVT-{int(datetime.utcnow().timestamp()*1000000)}"
def allocation_id(db): return f"ALC-{db.query(Allocation).count()+201:03}"

@router.get('/allocate/{request_id}')
def preview_allocation(request_id:str, db:Session=Depends(get_db)):
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==request_id).first()
    if not req: raise HTTPException(404,'Request not found')
    candidates=evaluate_candidates(db,req)
    selected=next((c for c in candidates if c['feasible']),None)
    if not selected: raise HTTPException(409,'No feasible resource/facility combination is currently available')
    return {'request':{'request_id':req.request_id,'location_name':req.location_name,'description':req.description,'triage_category':req.triage_category,'priority_score':req.priority_score,'required_resource':req.required_resource,'required_facility':req.required_facility},'selected':selected,'candidates':candidates}

@router.post('/allocate/{request_id}')
def create_allocation(request_id:str, db:Session=Depends(get_db)):
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==request_id).first()
    if not req: raise HTTPException(404,'Request not found')
    existing=db.query(Allocation).filter(Allocation.request_id==request_id,Allocation.status.in_(['RECOMMENDED','ACTIVE','DISPATCHED','EN_ROUTE'])).first()
    if existing: return {'allocation':existing,'created':False}
    candidates=evaluate_candidates(db,req); selected=next((c for c in candidates if c['feasible']),None)
    if not selected: raise HTTPException(409,'No feasible allocation available')
    aid=allocation_id(db)
    route=db.query(Route).filter(Route.origin_id==req.location_name,Route.destination_id==selected['facility_id']).first() if selected['facility_id'] else None
    allocation=Allocation(allocation_id=aid,request_id=req.request_id,resource_id=selected['resource_id'],facility_id=selected['facility_id'] or '',route_id=route.route_id if route else None,priority_score=req.priority_score,suitability_score=selected['score'],eta_minutes=selected['eta_minutes'],status='RECOMMENDED',decision_reason=' • '.join(selected['reasons']))
    req.status='ALLOCATED'; db.add(allocation)
    db.add(SystemEvent(event_id=event_id(),event_type='ALLOCATION_CREATED',request_id=req.request_id,allocation_id=aid,actor='Allocation Engine',message=f"{selected['resource_name']} → {selected['facility_name']} recommended • score {selected['score']}",reason=allocation.decision_reason))
    db.commit();db.refresh(allocation)
    return {'allocation':allocation,'selected':selected,'created':True}

@router.post('/dispatch/{allocation_id}')
def dispatch(allocation_id:str, db:Session=Depends(get_db)):
    a=db.query(Allocation).filter(Allocation.allocation_id==allocation_id).first()
    if not a: raise HTTPException(404,'Allocation not found')
    r=db.query(Resource).filter(Resource.resource_id==a.resource_id).first(); req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first()
    a.status='DISPATCHED'; a.updated_at=datetime.utcnow(); req.status='DISPATCHED'
    if r: r.status='DISPATCHED'; r.assigned_request=req.request_id
    db.add(SystemEvent(event_id=event_id(),event_type='DISPATCHED',request_id=req.request_id,allocation_id=a.allocation_id,actor='Command Center',message=f'{r.name if r else a.resource_id} dispatched for {req.request_id}'))
    db.commit();db.refresh(a);return a

@router.get('/allocations')
def list_allocations(db:Session=Depends(get_db)):
    return db.query(Allocation).order_by(Allocation.created_at.desc()).all()
