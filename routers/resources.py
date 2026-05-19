from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime, timezone
from database import get_db
from models import Problem, ProblemResource
import os
import uuid
import shutil

router = APIRouter(prefix="/resources", tags=["resources"])

# 文件上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")


class ResourceCreate(BaseModel):
    resource_type: Literal["link", "markdown", "pdf", "excel", "image"]
    name: str
    url: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    problem_id: int
    resource_type: str
    name: str
    url: Optional[str]
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/problems/{problem_id}", response_model=list[ResourceResponse])
def get_problem_resources(problem_id: int, db: Session = Depends(get_db)):
    """获取题目的资源列表"""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    return problem.resources


@router.post("/problems/{problem_id}", response_model=ResourceResponse)
def add_resource(problem_id: int, data: ResourceCreate, db: Session = Depends(get_db)):
    """添加资源（链接）"""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")

    if data.resource_type == "link" and not data.url:
        raise HTTPException(status_code=400, detail="链接类型必须提供 URL")

    resource = ProblemResource(
        problem_id=problem_id,
        resource_type=data.resource_type,
        name=data.name,
        url=data.url,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.post("/problems/{problem_id}/upload", response_model=ResourceResponse)
async def upload_file(problem_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传文件资源"""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 确定文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    type_map = {
        ".md": "markdown",
        ".pdf": "pdf",
        ".xlsx": "excel",
        ".xls": "excel",
        ".csv": "excel",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
    }
    resource_type = type_map.get(ext, "link")

    # 创建上传目录
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 保存文件（限制 10MB）
    max_size = 10 * 1024 * 1024
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        if len(content) > max_size:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        buffer.write(content)

    resource = ProblemResource(
        problem_id=problem_id,
        resource_type=resource_type,
        name=file.filename,
        file_path=file_path,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """删除资源"""
    resource = db.query(ProblemResource).filter(ProblemResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    # 如果是文件资源，删除文件
    if resource.file_path and os.path.exists(resource.file_path):
        os.remove(resource.file_path)

    db.delete(resource)
    db.commit()
    return {"message": "已删除"}


import mimetypes

# 浏览器可直接预览的资源类型
INLINE_TYPES = {"pdf", "image"}
MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
}


@router.get("/{resource_id}/download")
def download_file(resource_id: int, db: Session = Depends(get_db)):
    """下载/预览文件资源"""
    resource = db.query(ProblemResource).filter(ProblemResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    if not resource.file_path or not os.path.exists(resource.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = os.path.splitext(resource.name)[1].lower()
    media_type = MIME_MAP.get(ext) or mimetypes.guess_type(resource.name)[0] or "application/octet-stream"
    inline = resource.resource_type in INLINE_TYPES

    return FileResponse(
        resource.file_path,
        media_type=media_type,
        content_disposition_type="inline" if inline else "attachment",
        filename=resource.name,
    )
