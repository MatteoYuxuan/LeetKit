from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
import schemas
import crud

router = APIRouter(tags=["problems"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/problems")
def list_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: str | None = None,
    status: str | None = None,
    category_id: int | None = None,
    tag_id: int | None = None,
    q: str | None = None,
    sort_by: str = Query("leetcode_number", pattern="^(leetcode_number|difficulty|status|created_at|page_number)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    problems, total = crud.get_problems(
        db, page=page, page_size=page_size,
        difficulty=difficulty, status=status,
        category_id=category_id, tag_id=tag_id,
        q=q, sort_by=sort_by, sort_order=sort_order,
    )
    return {
        "items": [
            {
                "id": p.id,
                "leetcode_number": p.leetcode_number,
                "title": p.title,
                "title_cn": p.title_cn,
                "leetcode_slug": p.leetcode_slug,
                "page_number": p.page_number,
                "difficulty": p.difficulty,
                "status": p.status,
                "notes": p.notes,
                "solution_url": p.solution_url,
                "time_complexity": p.time_complexity,
                "space_complexity": p.space_complexity,
                "ac_rate": p.ac_rate,
                "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in p.categories],
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in p.tags],
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in problems
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/problems/{problem_id}")
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = crud.get_problem(db, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {
        "id": problem.id,
        "leetcode_number": problem.leetcode_number,
        "title": problem.title,
        "title_cn": problem.title_cn,
        "leetcode_slug": problem.leetcode_slug,
        "page_number": problem.page_number,
        "difficulty": problem.difficulty,
        "status": problem.status,
        "notes": problem.notes,
        "solution_url": problem.solution_url,
        "time_complexity": problem.time_complexity,
        "space_complexity": problem.space_complexity,
        "ac_rate": problem.ac_rate,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in problem.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in problem.tags],
        "created_at": problem.created_at.isoformat(),
        "updated_at": problem.updated_at.isoformat(),
    }


@router.post("/problems", status_code=201)
def create_problem(data: schemas.ProblemCreate, db: Session = Depends(get_db)):
    try:
        problem = crud.create_problem(db, data)
        return {
            "id": problem.id,
            "leetcode_number": problem.leetcode_number,
            "title": problem.title,
            "title_cn": problem.title_cn,
            "leetcode_slug": problem.leetcode_slug,
            "difficulty": problem.difficulty,
            "status": problem.status,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"题号 {data.leetcode_number} 已存在")


@router.put("/problems/{problem_id}")
def update_problem(problem_id: int, data: schemas.ProblemUpdate, db: Session = Depends(get_db)):
    try:
        problem = crud.update_problem(db, problem_id, data)
        if not problem:
            raise HTTPException(status_code=404, detail="题目不存在")
        return {
            "id": problem.id,
            "leetcode_number": problem.leetcode_number,
            "title": problem.title,
            "title_cn": problem.title_cn,
            "leetcode_slug": problem.leetcode_slug,
            "difficulty": problem.difficulty,
            "status": problem.status,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="数据冲突")


@router.delete("/problems/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    if not crud.delete_problem(db, problem_id):
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"detail": "删除成功"}
