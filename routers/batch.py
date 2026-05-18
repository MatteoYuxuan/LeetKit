from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from io import StringIO
import csv
from database import SessionLocal
from models import Problem, Note, Category, Tag

router = APIRouter(prefix="/batch", tags=["batch"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BatchIds(BaseModel):
    ids: list[int]


class BatchStatusUpdate(BaseModel):
    ids: list[int]
    status: str


class BatchCategoryUpdate(BaseModel):
    ids: list[int]
    category_ids: list[int]


class BatchTagUpdate(BaseModel):
    ids: list[int]
    tag_ids: list[int]


@router.post("/problems/delete")
def batch_delete_problems(data: BatchIds, db: Session = Depends(get_db)):
    problems = db.query(Problem).filter(Problem.id.in_(data.ids)).all()
    if not problems:
        raise HTTPException(status_code=404, detail="未找到题目")
    for p in problems:
        db.delete(p)
    db.commit()
    return {"deleted": len(problems)}


@router.post("/problems/status")
def batch_update_status(data: BatchStatusUpdate, db: Session = Depends(get_db)):
    valid_statuses = ["未做", "在做", "已解", "需复盘"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    problems = db.query(Problem).filter(Problem.id.in_(data.ids)).all()
    for p in problems:
        p.status = data.status
    db.commit()
    return {"updated": len(problems)}


@router.post("/problems/category")
def batch_add_category(data: BatchCategoryUpdate, db: Session = Depends(get_db)):
    problems = db.query(Problem).filter(Problem.id.in_(data.ids)).all()
    categories = db.query(Category).filter(Category.id.in_(data.category_ids)).all()
    if not categories:
        raise HTTPException(status_code=404, detail="未找到分类")
    for p in problems:
        for c in categories:
            if c not in p.categories:
                p.categories.append(c)
    db.commit()
    return {"updated": len(problems)}


@router.post("/problems/tag")
def batch_add_tag(data: BatchTagUpdate, db: Session = Depends(get_db)):
    problems = db.query(Problem).filter(Problem.id.in_(data.ids)).all()
    tags = db.query(Tag).filter(Tag.id.in_(data.tag_ids)).all()
    if not tags:
        raise HTTPException(status_code=404, detail="未找到标签")
    for p in problems:
        for t in tags:
            if t not in p.tags:
                p.tags.append(t)
    db.commit()
    return {"updated": len(problems)}


@router.post("/problems/export")
def batch_export_problems(data: BatchIds, db: Session = Depends(get_db)):
    problems = db.query(Problem).filter(Problem.id.in_(data.ids)).all()
    if not problems:
        raise HTTPException(status_code=404, detail="未找到题目")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["题号", "标题", "中文标题", "难度", "状态", "分类", "标签", "通过率"])

    for p in problems:
        categories = ";".join(c.name for c in p.categories)
        tags = ";".join(t.name for t in p.tags)
        writer.writerow([
            p.leetcode_number, p.title, p.title_cn or "",
            p.difficulty, p.status, categories, tags,
            f"{p.ac_rate:.1f}%" if p.ac_rate else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter(["﻿" + output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=problems_export.csv"},
    )


@router.post("/notes/delete")
def batch_delete_notes(data: BatchIds, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.id.in_(data.ids)).all()
    if not notes:
        raise HTTPException(status_code=404, detail="未找到笔记")
    for n in notes:
        db.delete(n)
    db.commit()
    return {"deleted": len(notes)}
