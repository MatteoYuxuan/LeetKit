from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
import schemas
import crud

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    categories = crud.get_categories(db)
    return [schemas.CategoryResponse(**c) for c in categories]


@router.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        cat = crud.create_category(db, data)
        return schemas.CategoryResponse.model_validate(cat)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"分类 '{data.name}' 已存在")


@router.put("/categories/{cat_id}", response_model=schemas.CategoryResponse)
def update_category(cat_id: int, data: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    try:
        cat = crud.update_category(db, cat_id, data)
        if not cat:
            raise HTTPException(status_code=404, detail="分类不存在")
        return schemas.CategoryResponse.model_validate(cat)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="分类名已存在")


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    success = crud.delete_category(db, cat_id)
    if not success:
        raise HTTPException(status_code=400, detail="分类不存在或仍有题目/笔记关联此分类")
    return {"detail": "删除成功"}
