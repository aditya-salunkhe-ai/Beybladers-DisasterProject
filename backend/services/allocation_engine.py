from math import radians, sin, cos, sqrt, atan2
from models import Resource, Facility, Route


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = radians(lat2-lat1); dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return r * 2 * atan2(sqrt(a), sqrt(1-a))


def facility_capability_ok(req, facility):
    need = (req.required_facility or '').upper()
    if facility.status == 'OFFLINE': return False, 'Facility offline'
    if need == 'ICU' and facility.available_icu <= 0: return False, 'ICU unavailable'
    if ('GENERAL' in need or 'BED' in need) and facility.available_beds <= 0: return False, 'Bed capacity unavailable'
    if facility.status == 'FULL': return False, 'Facility full'
    return True, None


def evaluate_candidates(db, req):
    resources = db.query(Resource).filter(Resource.resource_type == req.required_resource).all()
    facilities = db.query(Facility).all() if req.required_resource == 'Ambulance' else []
    candidates=[]

    if req.required_resource == 'Ambulance':
        for resource in resources:
            for facility in facilities:
                rejected=[]
                if resource.status != 'AVAILABLE': rejected.append(f'Resource {resource.status.lower()}')
                ok, why = facility_capability_ok(req, facility)
                if not ok: rejected.append(why)

                route = db.query(Route).filter(Route.origin_id == req.location_name, Route.destination_id == facility.facility_id).first()
                if route:
                    distance = route.distance_km; eta = route.eta_minutes; condition = route.condition
                    if not route.is_available or route.condition == 'BLOCKED': rejected.append('Route blocked')
                else:
                    distance = haversine_km(req.latitude, req.longitude, facility.latitude, facility.longitude)
                    eta = max(4, round(distance / 28 * 60))
                    condition = 'CLEAR'

                pickup_km = haversine_km(resource.latitude, resource.longitude, req.latitude, req.longitude)
                pickup_eta = max(2, round(pickup_km / 30 * 60))
                total_eta = pickup_eta + eta
                feasible = len(rejected)==0

                # Prototype suitability model: transparent deterministic weights.
                eta_score = max(0, 100 - total_eta*4)
                capacity_score = 100 if (req.required_facility or '').upper()=='ICU' and facility.available_icu>=3 else 85 if facility.available_beds>=10 else 65
                availability_score = 100 if resource.status=='AVAILABLE' else 0
                load_score = max(0, 100-resource.current_load*40)
                route_score = 100 if condition=='CLEAR' else 70 if condition=='CONGESTED' else 0
                score = round(.30*eta_score + .25*capacity_score + .20*availability_score + .15*load_score + .10*route_score) if feasible else 0
                reasons=[]
                if feasible:
                    reasons=[f'{req.triage_category} priority • score {req.priority_score}','Resource available',f'{req.required_facility or "Facility"} capacity available',f'Route {condition.lower()}',f'Estimated response + transfer: {total_eta} min']
                candidates.append({'resource_id':resource.resource_id,'resource_name':resource.name,'facility_id':facility.facility_id,'facility_name':facility.name,'eta_minutes':total_eta,'distance_km':round(distance+pickup_km,1),'route_condition':condition,'feasible':feasible,'score':score,'rejected_reasons':rejected,'reasons':reasons})
    else:
        for resource in resources:
            rejected=[] if resource.status=='AVAILABLE' else [f'Resource {resource.status.lower()}']
            dist=haversine_km(resource.latitude,resource.longitude,req.latitude,req.longitude); eta=max(3,round(dist/25*60)); feasible=not rejected
            score=max(0,round(100-eta*3-resource.current_load*10)) if feasible else 0
            candidates.append({'resource_id':resource.resource_id,'resource_name':resource.name,'facility_id':None,'facility_name':'Direct response','eta_minutes':eta,'distance_km':round(dist,1),'route_condition':'CLEAR','feasible':feasible,'score':score,'rejected_reasons':rejected,'reasons':[f'{req.triage_category} priority • score {req.priority_score}','Correct resource type','Resource available',f'ETA {eta} min'] if feasible else []})

    candidates.sort(key=lambda c:(c['feasible'],c['score']), reverse=True)
    return candidates
