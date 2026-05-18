from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import schemas
import crud

router = APIRouter(tags=["notes"])


@router.get("/notes", response_model=schemas.NoteListResponse)
def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    tag_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    notes, total = crud.get_notes(db, page=page, page_size=page_size, category_id=category_id, tag_id=tag_id, q=q)
    return schemas.NoteListResponse(
        items=[schemas.NoteResponse.model_validate(n) for n in notes],
        total=total, page=page, page_size=page_size,
    )


@router.get("/notes/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return schemas.NoteResponse.model_validate(note)


@router.post("/notes", response_model=schemas.NoteResponse, status_code=201)
def create_note(data: schemas.NoteCreate, db: Session = Depends(get_db)):
    note = crud.create_note(db, data)
    return schemas.NoteResponse.model_validate(note)


@router.put("/notes/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, data: schemas.NoteUpdate, db: Session = Depends(get_db)):
    note = crud.update_note(db, note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return schemas.NoteResponse.model_validate(note)


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    if not crud.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"detail": "删除成功"}
