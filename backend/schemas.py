from pydantic import BaseModel
from typing import Optional

class RequestCreate(BaseModel):
    location_name: str
    latitude: float = 19.076
    longitude: float = 72.877
    disaster_type: str = "Flood"
    request_type: str = "Medical"
    description: str
    people_affected: int = 1
    severity: str = "Critical"
    triage_category: str
    required_resource: str = "Ambulance"
    required_facility: Optional[str] = "ICU"
    waiting_minutes: int = 0
