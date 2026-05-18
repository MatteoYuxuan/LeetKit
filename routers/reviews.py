from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, ReviewRecord
import crud
import schemas

router = APIRouter(tags=["reviews"])


@router.get("/reviews/next", response_model=schemas.ReviewNextResponse | None)
def get_next_review(db: Session = Depends(get_db)):
    problem = crud.get_next_review(db)
    if not problem:
        return None
    review_count = len(problem.reviews)
    last_rating = max((r.rating for r in problem.reviews), default=None) if problem.reviews else None
    return schemas.ReviewNextResponse(
        problem=schemas.ProblemResponse.model_validate(problem),
        review_count=review_count,
        last_rating=last_rating,
    )


@router.post("/reviews", response_model=schemas.ReviewResponse, status_code=201)
def submit_review(data: schemas.ReviewSubmit, db: Session = Depends(get_db)):
    try:
        record = crud.submit_review(db, data.problem_id, data.rating)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return record


@router.get("/reviews/stats", response_model=schemas.ReviewStatsResponse)
def review_stats(db: Session = Depends(get_db)):
    return crud.get_review_stats(db)


@router.get("/reviews/today")
def today_reviews(db: Session = Depends(get_db)):
    return crud.get_today_reviews(db)
