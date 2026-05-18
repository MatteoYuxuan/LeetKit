from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Problem, ReviewRecord
import crud
import schemas

router = APIRouter(tags=["reviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/reviews/next")
def get_next_review(db: Session = Depends(get_db)):
    problem = crud.get_next_review(db)
    if not problem:
        return None
    review_count = db.query(ReviewRecord).filter(ReviewRecord.problem_id == problem.id).count()
    last_review = db.query(ReviewRecord).filter(ReviewRecord.problem_id == problem.id).order_by(ReviewRecord.created_at.desc()).first()
    last_rating = last_review.rating if last_review else None
    return {
        "problem": {
            "id": problem.id,
            "leetcode_number": problem.leetcode_number,
            "title": problem.title,
            "title_cn": problem.title_cn,
            "leetcode_slug": problem.leetcode_slug,
            "difficulty": problem.difficulty,
            "status": problem.status,
            "notes": problem.notes,
            "time_complexity": problem.time_complexity,
            "space_complexity": problem.space_complexity,
            "ac_rate": problem.ac_rate,
            "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in problem.categories],
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in problem.tags],
        },
        "review_count": review_count,
        "last_rating": last_rating,
    }


@router.post("/reviews", status_code=201)
def submit_review(data: schemas.ReviewSubmit, db: Session = Depends(get_db)):
    try:
        record = crud.submit_review(db, data.problem_id, data.rating)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": record.id,
        "problem_id": record.problem_id,
        "rating": record.rating,
        "interval": record.interval,
        "created_at": record.created_at.isoformat(),
    }


@router.get("/reviews/stats")
def review_stats(db: Session = Depends(get_db)):
    return crud.get_review_stats(db)


@router.get("/reviews/today")
def today_reviews(db: Session = Depends(get_db)):
    return crud.get_today_reviews(db)


@router.get("/reviews/timeline")
def review_timeline(db: Session = Depends(get_db)):
    return crud.get_review_timeline(db)
