from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud

router = APIRouter(tags=["stats"])


@router.get("/stats/overview", response_model=schemas.StatsOverview)
def stats_overview(db: Session = Depends(get_db)):
    return crud.get_stats_overview(db)


@router.get("/stats/by-category", response_model=list[schemas.CategoryStats])
def stats_by_category(db: Session = Depends(get_db)):
    return crud.get_stats_by_category(db)


@router.get("/stats/by-difficulty")
def stats_by_difficulty(db: Session = Depends(get_db)):
    return crud.get_stats_by_difficulty(db)


@router.get("/stats/progress", response_model=list[schemas.ProgressPoint])
def stats_progress(db: Session = Depends(get_db)):
    return crud.get_stats_progress(db)


@router.get("/stats/recent", response_model=list[schemas.ProblemResponse])
def stats_recent(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    problems = crud.get_stats_recent(db, limit)
    return [schemas.ProblemResponse.model_validate(p) for p in problems]


@router.get("/stats/heatmap")
def stats_heatmap(year: int = Query(None), db: Session = Depends(get_db)):
    return crud.get_stats_heatmap(db, year)


@router.post("/stats/reset-solved-at")
def reset_solved_at(db: Session = Depends(get_db)):
    return crud.reset_solved_at(db)
