from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db
from models import ProblemList, ProblemListItem, Problem, ReviewSchedule

router = APIRouter(tags=["problem-lists"])


class ProblemListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProblemListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProblemListItemCreate(BaseModel):
    problem_id: int
    sort_order: int = 0
    note: Optional[str] = None


class ReorderRequest(BaseModel):
    items: list[dict]  # [{"item_id": 1, "sort_order": 0}, ...]


class BatchAddItemsRequest(BaseModel):
    problem_ids: list[int]


class BatchAddByNumberRequest(BaseModel):
    leetcode_numbers: list[str]


@router.get("/problem-lists")
def list_problem_lists(db: Session = Depends(get_db)):
    lists = db.query(ProblemList).order_by(ProblemList.updated_at.desc()).all()
    result = []
    for pl in lists:
        status_counts = {}
        diff_counts = {}
        for item in pl.items:
            s = item.problem.status or '未做'
            d = item.problem.difficulty or 'EASY'
            status_counts[s] = status_counts.get(s, 0) + 1
            diff_counts[d] = diff_counts.get(d, 0) + 1
        solved = status_counts.get('已解', 0) + status_counts.get('需复盘', 0)
        result.append({
            "id": pl.id,
            "name": pl.name,
            "description": pl.description,
            "source": pl.source,
            "source_url": pl.source_url,
            "last_synced_at": pl.last_synced_at.isoformat() if pl.last_synced_at else None,
            "item_count": len(pl.items),
            "solved_count": solved,
            "status_counts": status_counts,
            "difficulty_counts": diff_counts,
            "created_at": pl.created_at.isoformat(),
            "updated_at": pl.updated_at.isoformat(),
        })
    return result


@router.get("/problem-lists/{list_id}")
def get_problem_list(list_id: int, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    return {
        "id": pl.id,
        "name": pl.name,
        "description": pl.description,
        "source": pl.source,
        "source_url": pl.source_url,
        "last_synced_at": pl.last_synced_at.isoformat() if pl.last_synced_at else None,
        "created_at": pl.created_at.isoformat(),
        "updated_at": pl.updated_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "problem_id": item.problem_id,
                "sort_order": item.sort_order,
                "note": item.note,
                "problem": {
                    "id": item.problem.id,
                    "leetcode_number": item.problem.leetcode_number,
                    "title": item.problem.title,
                    "title_cn": item.problem.title_cn,
                    "leetcode_slug": item.problem.leetcode_slug,
                    "difficulty": item.problem.difficulty,
                    "status": item.problem.status,
                    "categories": [c.name for c in item.problem.categories],
                    "tags": [t.name for t in item.problem.tags],
                },
            }
            for item in pl.items
        ],
    }


@router.post("/problem-lists", status_code=201)
def create_problem_list(data: ProblemListCreate, db: Session = Depends(get_db)):
    pl = ProblemList(name=data.name, description=data.description)
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return {"id": pl.id, "name": pl.name, "description": pl.description}


@router.put("/problem-lists/{list_id}")
def update_problem_list(list_id: int, data: ProblemListUpdate, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    if data.name is not None:
        pl.name = data.name
    if data.description is not None:
        pl.description = data.description
    db.commit()
    return {"id": pl.id, "name": pl.name, "description": pl.description}


@router.delete("/problem-lists/{list_id}")
def delete_problem_list(list_id: int, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    db.delete(pl)
    db.commit()
    return {"message": "删除成功"}


@router.post("/problem-lists/{list_id}/items", status_code=201)
def add_item_to_list(list_id: int, data: ProblemListItemCreate, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    problem = db.query(Problem).filter(Problem.id == data.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    existing = db.query(ProblemListItem).filter(
        ProblemListItem.problem_list_id == list_id,
        ProblemListItem.problem_id == data.problem_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="该题已在题单中")
    item = ProblemListItem(
        problem_list_id=list_id,
        problem_id=data.problem_id,
        sort_order=data.sort_order,
        note=data.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "problem_id": item.problem_id, "sort_order": item.sort_order}


@router.delete("/problem-lists/{list_id}/items/{item_id}")
def remove_item_from_list(list_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(ProblemListItem).filter(
        ProblemListItem.id == item_id,
        ProblemListItem.problem_list_id == list_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="题目不在题单中")
    db.delete(item)
    db.commit()
    return {"message": "移除成功"}


@router.put("/problem-lists/{list_id}/items/reorder")
def reorder_items(list_id: int, data: ReorderRequest, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    for item_data in data.items:
        item = db.query(ProblemListItem).filter(
            ProblemListItem.id == item_data["item_id"],
            ProblemListItem.problem_list_id == list_id,
        ).first()
        if item:
            item.sort_order = item_data.get("sort_order", 0)
    db.commit()
    return {"message": "排序更新成功"}


@router.post("/problem-lists/{list_id}/items/batch", status_code=201)
def batch_add_items(list_id: int, data: BatchAddItemsRequest, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")

    added = 0
    skipped = 0
    for problem_id in data.problem_ids:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            skipped += 1
            continue
        existing = db.query(ProblemListItem).filter(
            ProblemListItem.problem_list_id == list_id,
            ProblemListItem.problem_id == problem_id,
        ).first()
        if existing:
            skipped += 1
            continue
        item = ProblemListItem(
            problem_list_id=list_id,
            problem_id=problem_id,
            sort_order=len(pl.items) + added,
        )
        db.add(item)
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}


@router.post("/problem-lists/{list_id}/items/batch-by-number", status_code=201)
def batch_add_items_by_number(list_id: int, data: BatchAddByNumberRequest, db: Session = Depends(get_db)):
    """按 LeetCode 题号批量添加题目到题单"""
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")

    # 一次性查出所有匹配的 problem
    problems = db.query(Problem).filter(Problem.leetcode_number.in_(data.leetcode_numbers)).all()
    problem_map = {p.leetcode_number: p for p in problems}

    added = 0
    not_found = 0
    existing_count = len(pl.items)
    for num in data.leetcode_numbers:
        problem = problem_map.get(num)
        if not problem:
            not_found += 1
            continue
        existing = db.query(ProblemListItem).filter(
            ProblemListItem.problem_list_id == list_id,
            ProblemListItem.problem_id == problem.id,
        ).first()
        if existing:
            continue
        item = ProblemListItem(
            problem_list_id=list_id,
            problem_id=problem.id,
            sort_order=existing_count + added,
        )
        db.add(item)
        added += 1

    db.commit()
    return {"added": added, "not_found": not_found}


@router.get("/problem-lists/{list_id}/review-stats")
def get_list_review_stats(list_id: int, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    problem_ids = [item.problem_id for item in pl.items]
    if not problem_ids:
        return {"total": 0, "due": 0, "completed": 0, "not_scheduled": 0, "problem_ids": []}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # Get review schedules for these problems
    schedules = db.query(ReviewSchedule).filter(
        ReviewSchedule.problem_id.in_(problem_ids)
    ).all()

    schedule_map = {}
    for s in schedules:
        if s.problem_id not in schedule_map:
            schedule_map[s.problem_id] = []
        schedule_map[s.problem_id].append(s)

    due = 0
    completed = 0
    not_scheduled = 0
    for pid in problem_ids:
        pid_schedules = schedule_map.get(pid, [])
        if not pid_schedules:
            not_scheduled += 1
            continue
        active = [s for s in pid_schedules if not s.is_completed]
        if not active:
            completed += 1
        elif any(s.next_review_at and s.next_review_at <= now for s in active):
            due += 1

    return {
        "total": len(problem_ids),
        "due": due,
        "completed": completed,
        "not_scheduled": not_scheduled,
        "problem_ids": problem_ids,
    }
