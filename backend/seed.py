from database import Base, engine, SessionLocal
from models import EmergencyRequest, Resource, Facility, Route, SystemEvent
from services.priority_engine import calculate_priority
from datetime import datetime, timedelta

FACILITIES = [
("HSP-01","City General Hospital",19.085,72.890,120,18,20,3,"OPERATIONAL",76),
("HSP-02","Metro Care Hospital",19.060,72.865,150,24,25,5,"OPERATIONAL",68),
("HSP-03","District Medical Centre",19.100,72.910,80,9,10,1,"LIMITED",88),
("HSP-04","Community Hospital",19.045,72.900,60,6,6,0,"LIMITED",91),
("HSP-05","Regional Trauma Centre",19.115,72.875,100,14,16,4,"OPERATIONAL",73),]

REQUESTS = [
("Flood Zone A","Medical","Severe trauma patient","RED","Ambulance","ICU",4),
("Flood Zone C","Medical","Breathing difficulty","RED","Ambulance","ICU",2),
("Riverside Sector","Rescue","Trapped residents","RED","Rescue Vehicle",None,6),
("Zone B","Medical","Fracture requiring transport","YELLOW","Ambulance","General",13),
("Relief Camp North","Medicine","Essential medicines required","YELLOW","Medicine",None,18),
("Zone D","Food","Food packets required","GREEN","Food",None,21),
("Shelter East","Water","Drinking water shortage","YELLOW","Water",None,12),
("Zone E","Medical","Minor injuries","GREEN","Ambulance","General",17),
("Relief Camp South","Food","Food supplies low","GREEN","Food",None,25),
("Zone F","Medical","Elderly patient transport","YELLOW","Ambulance","General",9),
("Warehouse Corridor","Rescue","Debris clearance support","GREEN","Rescue Vehicle",None,8),
("Zone G","Medical","High fever and dehydration","YELLOW","Ambulance","General",11),]

def seed():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        for i,f in enumerate(FACILITIES,1):
            db.add(Facility(facility_id=f[0],name=f[1],facility_type="Hospital",latitude=f[2],longitude=f[3],total_beds=f[4],available_beds=f[5],total_icu=f[6],available_icu=f[7],status=f[8],current_load_pct=f[9]))
        for i in range(8):
            db.add(Resource(resource_id=f"AMB-{i+1:02}",name=f"Ambulance {chr(65+i)}",resource_type="Ambulance",latitude=19.05+i*.008,longitude=72.86+i*.006,status="AVAILABLE" if i<6 else "BUSY",capacity=2,current_load=0 if i<6 else 1))
        for i in range(3): db.add(Resource(resource_id=f"RES-{i+1:02}",name=f"Rescue Vehicle {i+1}",resource_type="Rescue Vehicle",latitude=19.07+i*.01,longitude=72.88+i*.01,status="AVAILABLE",capacity=6))
        # Relief resources used by the broader PPT scenario.
        db.add(Resource(resource_id="MED-01",name="Mobile Medical Team A",resource_type="Medical Team",latitude=19.082,longitude=72.884,status="AVAILABLE",capacity=4,current_load=0))
        db.add(Resource(resource_id="MEDS-01",name="Medicine Van A",resource_type="Medicine",latitude=19.064,longitude=72.872,status="AVAILABLE",capacity=40,current_load=0))
        db.add(Resource(resource_id="FOOD-01",name="Food Relief Truck A",resource_type="Food",latitude=19.092,longitude=72.898,status="AVAILABLE",capacity=100,current_load=0))
        db.add(Resource(resource_id="WATER-01",name="Water Tanker A",resource_type="Water",latitude=19.054,longitude=72.886,status="AVAILABLE",capacity=80,current_load=0))
        for i,r in enumerate(REQUESTS,1):
            triage=r[3]; score=calculate_priority(triage,r[6])
            db.add(EmergencyRequest(request_id=f"REQ-{104-i+1:03}",location_name=r[0],latitude=19.07+(i%5)*.009,longitude=72.87+(i%4)*.01,disaster_type="Flood",request_type=r[1],description=r[2],people_affected=1,severity="Critical" if triage=="RED" else "Urgent" if triage=="YELLOW" else "Minor",triage_category=triage,required_resource=r[4],required_facility=r[5],waiting_minutes=r[6],priority_score=score,status="PRIORITIZED"))
        # Route candidates from demo Zone A to each hospital
        for i,f in enumerate(FACILITIES,1):
            db.add(Route(route_id=f"ROUTE-{i:02}",origin_id="Flood Zone A",destination_id=f[0],distance_km=3.5+i*1.1,eta_minutes=4+i*2,condition="CONGESTED" if i==3 else "CLEAR",is_available=True))
        now=datetime.utcnow()
        events=[("REQUEST_CREATED","REQ-104","Critical medical request received"),("PRIORITY_ASSIGNED","REQ-104","RED triage assigned • Priority 100"),("STATE_UPDATE",None,"Hospital and resource capacities synchronized")]
        for i,e in enumerate(events,1): db.add(SystemEvent(event_id=f"EVT-{500+i}",timestamp=now-timedelta(minutes=5-i),event_type=e[0],request_id=e[1],message=e[2],actor="Beybladers State Engine"))
        db.commit()
    finally: db.close()

if __name__ == "__main__": seed(); print("Seeded Beybladers demo database.")
