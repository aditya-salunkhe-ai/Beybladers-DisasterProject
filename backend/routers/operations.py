from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import EmergencyRequest, Allocation, Resource, Facility, Route, SystemEvent
from services.allocation_engine import haversine_km, facility_capability_ok

router = APIRouter(prefix='/api', tags=['operations'])

def event_id(): return f"EVT-{int(datetime.utcnow().timestamp()*1000000)}"
def allocation_id(db): return f"ALC-{db.query(Allocation).count()+201:03}"

def mission_payload(db, a):
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first()
    res=db.query(Resource).filter(Resource.resource_id==a.resource_id).first()
    fac=db.query(Facility).filter(Facility.facility_id==a.facility_id).first() if a.facility_id else None
    route=db.query(Route).filter(Route.route_id==a.route_id).first() if a.route_id else None
    return {
        'allocation_id':a.allocation_id,'request_id':a.request_id,'status':a.status,'priority_score':a.priority_score,
        'suitability_score':a.suitability_score,'eta_minutes':a.eta_minutes,'decision_reason':a.decision_reason,
        'request': {'description':req.description,'location_name':req.location_name,'latitude':req.latitude,'longitude':req.longitude,'triage_category':req.triage_category,'required_facility':req.required_facility} if req else None,
        'resource': {'resource_id':res.resource_id,'name':res.name,'latitude':res.latitude,'longitude':res.longitude,'status':res.status} if res else None,
        'facility': {'facility_id':fac.facility_id,'name':fac.name,'latitude':fac.latitude,'longitude':fac.longitude,'available_icu':fac.available_icu,'available_beds':fac.available_beds,'status':fac.status} if fac else None,
        'route': {'route_id':route.route_id,'condition':route.condition,'is_available':route.is_available,'eta_minutes':route.eta_minutes} if route else None,
    }

def best_new_destination(db, req, resource, exclude_facility=None):
    options=[]
    for fac in db.query(Facility).all():
        if fac.facility_id==exclude_facility: continue
        ok, why=facility_capability_ok(req,fac)
        if not ok: continue
        route=db.query(Route).filter(Route.origin_id==req.location_name,Route.destination_id==fac.facility_id).first()
        if route and (not route.is_available or route.condition=='BLOCKED'): continue
        transfer_eta=route.eta_minutes if route else max(4,round(haversine_km(req.latitude,req.longitude,fac.latitude,fac.longitude)/28*60))
        pickup_eta=max(2,round(haversine_km(resource.latitude,resource.longitude,req.latitude,req.longitude)/30*60))
        total=pickup_eta+transfer_eta
        cap=100 if (req.required_facility or '').upper()=='ICU' and fac.available_icu>=3 else 85 if fac.available_beds>=10 else 65
        route_score=100 if not route or route.condition=='CLEAR' else 70
        score=round(.30*max(0,100-total*4)+.25*cap+.20*100+.15*max(0,100-resource.current_load*40)+.10*route_score)
        options.append((score,total,fac,route))
    return max(options,key=lambda x:x[0]) if options else None

def reallocate(db, current, reason):
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==current.request_id).first()
    res=db.query(Resource).filter(Resource.resource_id==current.resource_id).first()
    if not req or not res: raise HTTPException(409,'Active mission data is incomplete')
    best=best_new_destination(db,req,res,current.facility_id)
    if not best: raise HTTPException(409,'No feasible alternate destination is available')
    score,eta,fac,route=best
    old_fac=db.query(Facility).filter(Facility.facility_id==current.facility_id).first()
    old_name=old_fac.name if old_fac else current.facility_id
    current.status='SUPERSEDED'; current.updated_at=datetime.utcnow()
    aid=allocation_id(db)
    new=Allocation(allocation_id=aid,request_id=req.request_id,resource_id=res.resource_id,facility_id=fac.facility_id,route_id=route.route_id if route else None,priority_score=req.priority_score,suitability_score=score,eta_minutes=eta,status='EN_ROUTE',decision_reason=f'Re-optimized after live state change • {reason} • alternate destination feasible',created_at=datetime.utcnow(),updated_at=datetime.utcnow())
    req.status='EN_ROUTE'; res.status='EN_ROUTE'; res.assigned_request=req.request_id
    db.add(new)
    db.add(SystemEvent(event_id=event_id(),event_type='REOPTIMIZATION_TRIGGERED',request_id=req.request_id,allocation_id=current.allocation_id,actor='State Engine',message=f'Current allocation invalidated: {reason}',reason=reason))
    db.add(SystemEvent(event_id=event_id(),event_type='REALLOCATION_CREATED',request_id=req.request_id,allocation_id=aid,actor='Allocation Engine',message=f'{old_name} → {fac.name} • new ETA {eta} min',previous_value=old_name,new_value=fac.name,reason=reason))
    db.commit(); db.refresh(new)
    return {'reoptimized':True,'reason':reason,'previous_facility':old_name,'new_facility':fac.name,'new_eta':eta,'allocation':mission_payload(db,new)}

@router.get('/operations/missions')
def missions(db:Session=Depends(get_db)):
    rows=db.query(Allocation).filter(Allocation.status.in_(['DISPATCHED','EN_ROUTE'])).order_by(Allocation.updated_at.desc()).all()
    return [mission_payload(db,a) for a in rows]

@router.post('/operations/{allocation_id}/en-route')
def mark_en_route(allocation_id:str,db:Session=Depends(get_db)):
    a=db.query(Allocation).filter(Allocation.allocation_id==allocation_id).first()
    if not a: raise HTTPException(404,'Allocation not found')
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first(); res=db.query(Resource).filter(Resource.resource_id==a.resource_id).first()
    a.status='EN_ROUTE'; a.updated_at=datetime.utcnow()
    if req: req.status='EN_ROUTE'
    if res: res.status='EN_ROUTE'
    db.add(SystemEvent(event_id=event_id(),event_type='EN_ROUTE',request_id=a.request_id,allocation_id=a.allocation_id,actor='Command Center',message=f'{res.name if res else a.resource_id} is en route'))
    db.commit(); return mission_payload(db,a)

@router.post('/simulate/facility-full/{allocation_id}')
def facility_full(allocation_id:str,db:Session=Depends(get_db)):
    a=db.query(Allocation).filter(Allocation.allocation_id==allocation_id,Allocation.status.in_(['DISPATCHED','EN_ROUTE'])).first()
    if not a: raise HTTPException(404,'Active allocation not found')
    fac=db.query(Facility).filter(Facility.facility_id==a.facility_id).first()
    if not fac: raise HTTPException(404,'Facility not found')
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first()
    previous=f'ICU {fac.available_icu} • Beds {fac.available_beds}'
    if (req.required_facility or '').upper()=='ICU': fac.available_icu=0
    else: fac.available_beds=0
    fac.status='FULL' if fac.available_beds==0 and fac.available_icu==0 else 'LIMITED'; fac.last_updated=datetime.utcnow()
    db.add(SystemEvent(event_id=event_id(),event_type='FACILITY_CAPACITY_CHANGED',request_id=req.request_id,allocation_id=a.allocation_id,actor='Demo Simulator',message=f'{fac.name} required capacity became unavailable',previous_value=previous,new_value=f'ICU {fac.available_icu} • Beds {fac.available_beds}',reason='Simulated live capacity update'))
    db.flush()
    return reallocate(db,a,f'Required {req.required_facility or "facility"} capacity unavailable at {fac.name}')

@router.post('/simulate/road-block/{allocation_id}')
def road_block(allocation_id:str,db:Session=Depends(get_db)):
    a=db.query(Allocation).filter(Allocation.allocation_id==allocation_id,Allocation.status.in_(['DISPATCHED','EN_ROUTE'])).first()
    if not a: raise HTTPException(404,'Active allocation not found')
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first()
    route=db.query(Route).filter(Route.route_id==a.route_id).first() if a.route_id else db.query(Route).filter(Route.origin_id==req.location_name,Route.destination_id==a.facility_id).first()
    if not route: raise HTTPException(409,'This mission has no simulated route to block')
    route.condition='BLOCKED'; route.is_available=False
    fac=db.query(Facility).filter(Facility.facility_id==a.facility_id).first()
    db.add(SystemEvent(event_id=event_id(),event_type='ROUTE_BLOCKED',request_id=req.request_id,allocation_id=a.allocation_id,actor='Demo Simulator',message=f'Route to {fac.name if fac else a.facility_id} blocked',previous_value='CLEAR/AVAILABLE',new_value='BLOCKED',reason='Simulated road disruption'))
    db.flush()
    return reallocate(db,a,f'Route to {fac.name if fac else a.facility_id} blocked')

@router.post('/operations/{allocation_id}/deliver')
def confirm_delivery(allocation_id:str,db:Session=Depends(get_db)):
    a=db.query(Allocation).filter(Allocation.allocation_id==allocation_id,Allocation.status.in_(['DISPATCHED','EN_ROUTE'])).first()
    if not a: raise HTTPException(404,'Active allocation not found')
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==a.request_id).first()
    res=db.query(Resource).filter(Resource.resource_id==a.resource_id).first()
    fac=db.query(Facility).filter(Facility.facility_id==a.facility_id).first() if a.facility_id else None
    a.status='DELIVERED'; a.updated_at=datetime.utcnow()
    if req: req.status='DELIVERED'
    if res:
        res.status='AVAILABLE'; res.assigned_request=None; res.current_load=0; res.last_updated=datetime.utcnow()
    if fac and req:
        if (req.required_facility or '').upper()=='ICU' and fac.available_icu>0: fac.available_icu-=1
        elif fac.available_beds>0: fac.available_beds-=1
        fac.last_updated=datetime.utcnow()
    db.add(SystemEvent(event_id=event_id(),event_type='DELIVERY_CONFIRMED',request_id=a.request_id,allocation_id=a.allocation_id,actor='Field / Dispatch Team',message=f'Delivery/admission confirmed at {fac.name if fac else a.facility_id}',new_value='DELIVERED',reason='Prototype delivery confirmation'))
    db.commit(); db.refresh(a)
    return {'verified':True,'message':'Delivery confirmed and mission closed','allocation':mission_payload(db,a)}

@router.get('/audit/requests/{request_id}')
def request_audit(request_id:str,db:Session=Depends(get_db)):
    req=db.query(EmergencyRequest).filter(EmergencyRequest.request_id==request_id).first()
    if not req: raise HTTPException(404,'Request not found')
    allocations=db.query(Allocation).filter(Allocation.request_id==request_id).order_by(Allocation.created_at.asc()).all()
    events=db.query(SystemEvent).filter(SystemEvent.request_id==request_id).order_by(SystemEvent.timestamp.asc()).all()
    return {'request':{'request_id':req.request_id,'description':req.description,'location_name':req.location_name,'triage_category':req.triage_category,'priority_score':req.priority_score,'status':req.status},'allocations':[mission_payload(db,a) for a in allocations],'events':events,'event_count':len(events),'trace_complete':req.status in ['DELIVERED','CLOSED']}
