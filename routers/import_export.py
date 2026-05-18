import csv
import io
import json
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, Category, Tag, Note
import crud
import schemas

router = APIRouter(tags=["import-export"])


@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    categories = crud.get_categories(db)
    tags = crud.get_tags(db)
    problems, _ = crud.get_problems(db, page=1, page_size=100000)

    data = {
        "exported_at": datetime.now().isoformat(),
        "categories": [{"name": c["name"], "description": c.get("description"), "color": c.get("color")} for c in categories],
        "tags": [{"name": t["name"], "color": t.get("color")} for t in tags],
        "problems": [],
    }
    for p in problems:
        data["problems"].append({
            "leetcode_number": p.leetcode_number,
            "title": p.title,
            "title_cn": p.title_cn,
            "page_number": p.page_number,
            "difficulty": p.difficulty,
            "status": p.status,
            "categories": [c.name for c in p.categories],
            "tags": [t.name for t in p.tags],
            "notes": p.notes,
            "solution_url": p.solution_url,
            "time_complexity": p.time_complexity,
            "space_complexity": p.space_complexity,
        })

    notes, _ = crud.get_notes(db, page=1, page_size=100000)
    data["notes"] = []
    for n in notes:
        data["notes"].append({
            "title": n.title,
            "page_number": n.page_number,
            "categories": [c.name for c in n.categories],
            "tags": [t.name for t in n.tags],
            "content": n.content,
        })

    content = json.dumps(data, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=notebook_export.json"},
    )


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    problems, _ = crud.get_problems(db, page=1, page_size=100000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "leetcode_number", "title", "title_cn", "page_number",
        "difficulty", "status", "categories", "tags",
        "notes", "solution_url", "time_complexity", "space_complexity",
    ])
    for p in problems:
        writer.writerow([
            p.leetcode_number, p.title, p.title_cn, p.page_number,
            p.difficulty, p.status,
            ";".join(c.name for c in p.categories),
            ";".join(t.name for t in p.tags),
            p.notes, p.solution_url,
            p.time_complexity, p.space_complexity,
        ])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=notebook_problems.csv"},
    )


@router.get("/export/notes/csv")
def export_notes_csv(db: Session = Depends(get_db)):
    notes, _ = crud.get_notes(db, page=1, page_size=100000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["title", "page_number", "categories", "tags", "content"])
    for n in notes:
        writer.writerow([
            n.title, n.page_number,
            ";".join(c.name for c in n.categories),
            ";".join(t.name for t in n.tags),
            n.content,
        ])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=notebook_notes.csv"},
    )


@router.post("/import/json", response_model=schemas.ImportResult)
async def import_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")

    imported = 0
    skipped = 0
    errors = []

    existing_cat = {c["name"]: c["id"] for c in crud.get_categories(db)}
    existing_tag = {t["name"]: t["id"] for t in crud.get_tags(db)}

    for cat_data in data.get("categories", []):
        name = cat_data.get("name")
        if name and name not in existing_cat:
            cat = crud.create_category(db, schemas.CategoryCreate(name=name, description=cat_data.get("description"), color=cat_data.get("color")))
            existing_cat[name] = cat.id

    for tag_data in data.get("tags", []):
        name = tag_data.get("name")
        if name and name not in existing_tag:
            tag = crud.create_tag(db, schemas.TagCreate(name=name, color=tag_data.get("color")))
            existing_tag[name] = tag.id

    for p in data.get("problems", []):
        lc_num = p.get("leetcode_number")
        if not lc_num:
            errors.append(f"跳过: 缺少 leetcode_number")
            continue
        try:
            cat_names = p.get("categories") or []
            if not cat_names and p.get("category"):
                cat_names = [p["category"]]
            cat_ids = [existing_cat[n] for n in cat_names if n in existing_cat]
            tag_names = p.get("tags", [])
            tag_ids = [existing_tag[n] for n in tag_names if n in existing_tag]

            problem_data = schemas.ProblemCreate(
                leetcode_number=lc_num,
                title=p.get("title", f"Problem {lc_num}"),
                title_cn=p.get("title_cn"),
                page_number=p.get("page_number"),
                difficulty=p.get("difficulty", "MEDIUM"),
                status=p.get("status", "未做"),
                category_ids=cat_ids,
                notes=p.get("notes"),
                solution_url=p.get("solution_url"),
                time_complexity=p.get("time_complexity"),
                space_complexity=p.get("space_complexity"),
                tag_ids=tag_ids,
            )
            crud.create_problem(db, problem_data)
            imported += 1
        except Exception as e:
            db.rollback()
            skipped += 1
            errors.append(f"题目 #{lc_num}: {str(e)}")

    for n in data.get("notes", []):
        title = n.get("title")
        if not title:
            errors.append("跳过笔记: 缺少 title")
            continue
        try:
            cat_names = n.get("categories") or []
            if not cat_names and n.get("category"):
                cat_names = [n["category"]]
            cat_ids = [existing_cat[c] for c in cat_names if c in existing_cat]
            tag_names = n.get("tags", [])
            tag_ids = [existing_tag[t] for t in tag_names if t in existing_tag]
            note_data = schemas.NoteCreate(
                title=title,
                page_number=n.get("page_number"),
                category_ids=cat_ids,
                content=n.get("content"),
                tag_ids=tag_ids,
            )
            crud.create_note(db, note_data)
            imported += 1
        except Exception as e:
            db.rollback()
            skipped += 1
            errors.append(f"笔记 \"{title}\": {str(e)}")

    return schemas.ImportResult(imported=imported, skipped=skipped, errors=errors)


@router.post("/import/csv", response_model=schemas.ImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("gbk")

    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    errors = []

    existing_cat = {c["name"]: c["id"] for c in crud.get_categories(db)}
    existing_tag = {t["name"]: t["id"] for t in crud.get_tags(db)}

    for row in reader:
        lc_num = row.get("leetcode_number")
        if not lc_num:
            errors.append("跳过: 缺少 leetcode_number")
            continue
        try:
            cat_str = row.get("categories", row.get("category", "")).strip()
            cat_names = [c.strip() for c in cat_str.split(";") if c.strip()] if cat_str else []
            cat_ids = []
            for cn in cat_names:
                if cn not in existing_cat:
                    cat = crud.create_category(db, schemas.CategoryCreate(name=cn))
                    existing_cat[cn] = cat.id
                cat_ids.append(existing_cat[cn])

            tag_str = row.get("tags", "").strip()
            tag_names = [t.strip() for t in tag_str.split(";") if t.strip()] if tag_str else []
            tag_ids = []
            for tn in tag_names:
                if tn not in existing_tag:
                    tag = crud.create_tag(db, schemas.TagCreate(name=tn))
                    existing_tag[tn] = tag.id
                tag_ids.append(existing_tag[tn])

            problem_data = schemas.ProblemCreate(
                leetcode_number=str(lc_num),
                title=row.get("title", f"Problem {lc_num}"),
                title_cn=row.get("title_cn") or None,
                page_number=int(row["page_number"]) if row.get("page_number") else None,
                difficulty=row.get("difficulty", "MEDIUM"),
                status=row.get("status", "未做"),
                category_ids=cat_ids,
                notes=row.get("notes") or None,
                solution_url=row.get("solution_url") or None,
                time_complexity=row.get("time_complexity") or None,
                space_complexity=row.get("space_complexity") or None,
                tag_ids=tag_ids,
            )
            crud.create_problem(db, problem_data)
            imported += 1
        except Exception as e:
            db.rollback()
            skipped += 1
            errors.append(f"题目 #{lc_num}: {str(e)}")

    return schemas.ImportResult(imported=imported, skipped=skipped, errors=errors)
