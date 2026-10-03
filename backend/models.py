from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime
from database import Base

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    id=Column(Integer, primary_key=True); request_id=Column(String, unique=True, index=True)
    created_at=Column(DateTime, default=datetime.utcnow); location_name=Column(String); latitude=Column(Float); longitude=Column(Float)
    disaster_type=Column(String); request_type=Column(String); description=Column(Text); people_affected=Column(Integer, default=1)
    severity=Column(String); triage_category=Column(String); required_resource=Column(String); required_facility=Column(String, nullable=True)
    waiting_minutes=Column(Integer, default=0); priority_score=Column(Integer, default=0); status=Column(String, default="PENDING")

class Resource(Base):
    __tablename__="resources"
    id=Column(Integer, primary_key=True); resource_id=Column(String, unique=True); name=Column(String); resource_type=Column(String)
    latitude=Column(Float); longitude=Column(Float); status=Column(String, default="AVAILABLE"); capacity=Column(Integer, default=1)
    current_load=Column(Integer, default=0); assigned_request=Column(String, nullable=True); last_updated=Column(DateTime, default=datetime.utcnow)

class Facility(Base):
    __tablename__="facilities"
    id=Column(Integer, primary_key=True); facility_id=Column(String, unique=True); name=Column(String); facility_type=Column(String)
    latitude=Column(Float); longitude=Column(Float); total_beds=Column(Integer, default=0); available_beds=Column(Integer, default=0)
    total_icu=Column(Integer, default=0); available_icu=Column(Integer, default=0); status=Column(String, default="OPERATIONAL")
    current_load_pct=Column(Integer, default=0); last_updated=Column(DateTime, default=datetime.utcnow)

class Route(Base):
    __tablename__="routes"
    id=Column(Integer, primary_key=True); route_id=Column(String, unique=True); origin_id=Column(String); destination_id=Column(String)
    distance_km=Column(Float); eta_minutes=Column(Integer); condition=Column(String, default="CLEAR"); is_available=Column(Boolean, default=True)

class Allocation(Base):
    __tablename__="allocations"
    id=Column(Integer, primary_key=True); allocation_id=Column(String, unique=True); request_id=Column(String); resource_id=Column(String)
    facility_id=Column(String); route_id=Column(String, nullable=True); priority_score=Column(Integer); suitability_score=Column(Integer)
    eta_minutes=Column(Integer); status=Column(String, default="ACTIVE"); decision_reason=Column(Text); created_at=Column(DateTime, default=datetime.utcnow); updated_at=Column(DateTime, default=datetime.utcnow)

class SystemEvent(Base):
    __tablename__="system_events"
    id=Column(Integer, primary_key=True); event_id=Column(String, unique=True); timestamp=Column(DateTime, default=datetime.utcnow)
    event_type=Column(String); request_id=Column(String, nullable=True); allocation_id=Column(String, nullable=True); actor=Column(String, default="System")
    message=Column(Text); previous_value=Column(String, nullable=True); new_value=Column(String, nullable=True); reason=Column(Text, nullable=True)
