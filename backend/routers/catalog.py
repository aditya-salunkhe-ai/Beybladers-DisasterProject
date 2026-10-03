from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Resource,Facility,SystemEvent
router=APIRouter(prefix="/api",tags=["state"])
@router.get("/resources")
def resources(db:Session=Depends(get_db)): return db.query(Resource).all()
@router.get("/facilities")
def facilities(db:Session=Depends(get_db)): return db.query(Facility).all()
@router.get("/events")
def events(db:Session=Depends(get_db)): return db.query(SystemEvent).order_by(SystemEvent.timestamp.desc()).limit(50).all()
