from database import Base, engine, SessionLocal
from models import EmergencyRequest
from seed import seed


def ensure_seeded():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(EmergencyRequest).count() == 0:
            db.close()
            seed()
            return
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == "__main__":
    ensure_seeded()
