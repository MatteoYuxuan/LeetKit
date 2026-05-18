from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import schemas
import crud

router = APIRouter(tags=["tags"])


@router.get("/tags", response_model=list[schemas.TagResponse])
def list_tags(db: Session = Depends(get_db)):
    tags = crud.get_tags(db)
    return [schemas.TagResponse(**t) for t in tags]


@router.post("/tags", response_model=schemas.TagResponse, status_code=201)
def create_tag(data: schemas.TagCreate, db: Session = Depends(get_db)):
    try:
        tag = crud.create_tag(db, data)
        return schemas.TagResponse.model_validate(tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"标签 '{data.name}' 已存在")


@router.put("/tags/{tag_id}", response_model=schemas.TagResponse)
def update_tag(tag_id: int, data: schemas.TagUpdate, db: Session = Depends(get_db)):
    try:
        tag = crud.update_tag(db, tag_id, data)
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        return schemas.TagResponse.model_validate(tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="标签名已存在")


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    if not crud.delete_tag(db, tag_id):
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"detail": "删除成功"}
