from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal
from models import Problem, Note, ProblemList

router = APIRouter(tags=["search"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|problems|notes|lists)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = {"problems": [], "notes": [], "problem_lists": []}
    pattern = f"%{q}%"

    if type in ("all", "problems"):
        problems = db.query(Problem).filter(
            or_(
                Problem.title.ilike(pattern),
                Problem.title_cn.ilike(pattern),
                Problem.notes.ilike(pattern),
                Problem.leetcode_number.cast(str).ilike(pattern),
            )
        ).limit(limit).all()
        results["problems"] = [
            {
                "id": p.id,
                "leetcode_number": p.leetcode_number,
                "title": p.title,
                "title_cn": p.title_cn,
                "difficulty": p.difficulty,
                "status": p.status,
            }
            for p in problems
        ]

    if type in ("all", "notes"):
        notes = db.query(Note).filter(
            or_(
                Note.title.ilike(pattern),
                Note.content.ilike(pattern),
            )
        ).limit(limit).all()
        results["notes"] = [
            {
                "id": n.id,
                "title": n.title,
                "snippet": (n.content[:100] + "...") if n.content and len(n.content) > 100 else n.content,
            }
            for n in notes
        ]

    if type in ("all", "lists"):
        lists = db.query(ProblemList).filter(
            or_(
                ProblemList.name.ilike(pattern),
                ProblemList.description.ilike(pattern),
            )
        ).limit(limit).all()
        results["problem_lists"] = [
            {"id": pl.id, "name": pl.name, "description": pl.description}
            for pl in lists
        ]

    return results
