import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Note
import schemas
import crud

router = APIRouter(tags=["notes"])

NOTES_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "notes_files")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/notes")
def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    tag_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    notes, total = crud.get_notes(db, page=page, page_size=page_size, category_id=category_id, tag_id=tag_id, q=q)
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "page_number": n.page_number,
                "content": n.content,
                "format": n.format,
                "file_path": n.file_path,
                "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in n.categories],
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in n.tags],
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in notes
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/notes/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {
        "id": note.id,
        "title": note.title,
        "page_number": note.page_number,
        "content": note.content,
        "format": note.format,
        "file_path": note.file_path,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in note.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in note.tags],
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.post("/notes", status_code=201)
def create_note(data: schemas.NoteCreate, db: Session = Depends(get_db)):
    note = crud.create_note(db, data)
    return {
        "id": note.id,
        "title": note.title,
        "page_number": note.page_number,
        "content": note.content,
        "format": note.format,
        "file_path": note.file_path,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in note.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in note.tags],
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.put("/notes/{note_id}")
def update_note(note_id: int, data: schemas.NoteUpdate, db: Session = Depends(get_db)):
    note = crud.update_note(db, note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {
        "id": note.id,
        "title": note.title,
        "page_number": note.page_number,
        "content": note.content,
        "format": note.format,
        "file_path": note.file_path,
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in note.categories],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in note.tags],
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    if not crud.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"detail": "删除成功"}


@router.post("/notes/{note_id}/upload-pdf")
async def upload_pdf(note_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    # 创建目录
    note_dir = os.path.join(NOTES_FILES_DIR, str(note_id))
    os.makedirs(note_dir, exist_ok=True)

    # 保存文件
    filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(note_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 更新数据库
    note.file_path = f"{note_id}/{filename}"
    note.format = "pdf"
    db.commit()

    return {"message": "上传成功", "file_path": note.file_path}


@router.get("/notes/{note_id}/download-pdf")
def download_pdf(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note or not note.file_path:
        raise HTTPException(status_code=404, detail="PDF 文件不存在")

    file_path = os.path.join(NOTES_FILES_DIR, note.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF 文件不存在")

    return FileResponse(
        path=file_path,
        filename=f"{note.title}.pdf",
        media_type="application/pdf",
    )


@router.delete("/notes/{note_id}/file")
def delete_file(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if note.file_path:
        file_path = os.path.join(NOTES_FILES_DIR, note.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        note.file_path = None
        note.format = "markdown"
        db.commit()

    return {"message": "文件删除成功"}


@router.post("/notes/{note_id}/export-pdf")
def export_pdf(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if not note.content:
        raise HTTPException(status_code=400, detail="笔记内容为空")

    try:
        import markdown
        from xhtml2pdf import pisa

        # Markdown 转 HTML
        html_content = markdown.markdown(
            note.content,
            extensions=['fenced_code', 'tables', 'codehilite']
        )
        full_html = f"""
        <html><head>
        <style>
            body {{ font-family: sans-serif; padding: 40px; }}
            code {{ background: #f3f3f3; padding: 2px 6px; border-radius: 4px; }}
            pre {{ background: #f3f3f3; padding: 12px; border-radius: 6px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        </style>
        </head><body>{html_content}</body></html>
        """

        # 创建目录
        note_dir = os.path.join(NOTES_FILES_DIR, str(note_id))
        os.makedirs(note_dir, exist_ok=True)

        # 生成 PDF
        filename = f"{uuid.uuid4().hex}.pdf"
        file_path = os.path.join(note_dir, filename)

        with open(file_path, "wb") as f:
            pisa_status = pisa.CreatePDF(full_html, dest=f)
            if pisa_status.err:
                raise Exception("PDF 生成失败")

        # 更新数据库
        note.file_path = f"{note_id}/{filename}"
        note.format = "pdf"
        db.commit()

        return FileResponse(
            path=file_path,
            filename=f"{note.title}.pdf",
            media_type="application/pdf",
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF 生成依赖未安装，请安装 xhtml2pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {str(e)}")
