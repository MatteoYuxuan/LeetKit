from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import SessionLocal
from models import ProblemList, ProblemListItem, Problem

router = APIRouter(tags=["problem-lists"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ProblemListCreate(BaseModel):
    name: str
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


@router.get("/problem-lists")
def list_problem_lists(db: Session = Depends(get_db)):
    lists = db.query(ProblemList).order_by(ProblemList.updated_at.desc()).all()
    return [
        {
            "id": pl.id,
            "name": pl.name,
            "description": pl.description,
            "item_count": len(pl.items),
            "created_at": pl.created_at.isoformat(),
            "updated_at": pl.updated_at.isoformat(),
        }
        for pl in lists
    ]


@router.get("/problem-lists/{list_id}")
def get_problem_list(list_id: int, db: Session = Depends(get_db)):
    pl = db.query(ProblemList).filter(ProblemList.id == list_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="题单不存在")
    return {
        "id": pl.id,
        "name": pl.name,
        "description": pl.description,
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
                    "difficulty": item.problem.difficulty,
                    "status": item.problem.status,
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
