from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import crud

router = APIRouter(tags=["checkin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/checkin")
def do_checkin(db: Session = Depends(get_db)):
    return crud.checkin_today(db)


@router.get("/checkin/stats")
def checkin_stats(db: Session = Depends(get_db)):
    return crud.get_checkin_stats(db)
