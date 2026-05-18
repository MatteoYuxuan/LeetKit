from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import SessionLocal
from models import Problem, LeetCodeCookie, Category
from crawler.leetcode_client import LeetCodeClient

router = APIRouter(prefix="/leetcode", tags=["leetcode"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CookieLogin(BaseModel):
    cookie: str


class ImportRequest(BaseModel):
    problems: list[dict]  # [{"frontendQuestionId": "1", "title": "Two Sum", ...}]


@router.post("/login")
async def login(data: CookieLogin, db: Session = Depends(get_db)):
    try:
        client = LeetCodeClient(cookie=data.cookie)
        result = await client.verify_cookie()
        if not result["is_signed_in"]:
            raise HTTPException(status_code=401, detail="Cookie 无效或已过期")

        # 清除旧 cookie
        db.query(LeetCodeCookie).delete()

        cookie_record = LeetCodeCookie(
            cookie_value=data.cookie,
            leetcode_username=result["username"],
            is_active=1,
            last_validated_at=datetime.now(timezone.utc),
        )
        db.add(cookie_record)
        db.commit()

        return {"message": "登录成功", "username": result["username"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    cookie = db.query(LeetCodeCookie).filter(LeetCodeCookie.is_active == 1).first()
    if not cookie:
        return {"logged_in": False, "username": None}
    return {
        "logged_in": True,
        "username": cookie.leetcode_username,
        "last_validated_at": cookie.last_validated_at.isoformat() if cookie.last_validated_at else None,
    }


@router.delete("/logout")
def logout(db: Session = Depends(get_db)):
    db.query(LeetCodeCookie).delete()
    db.commit()
    return {"message": "已退出登录"}


@router.get("/search")
async def search_problems(
    q: str = "",
    difficulty: str = None,
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    try:
        cookie = db.query(LeetCodeCookie).filter(LeetCodeCookie.is_active == 1).first()
        client = LeetCodeClient(cookie=cookie.cookie_value if cookie else None)
        result = await client.search_problems(
            keyword=q if q else None,
            limit=limit,
            skip=skip,
            difficulty=difficulty,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/import")
def import_problems(data: ImportRequest, db: Session = Depends(get_db)):
    imported = 0
    skipped = 0
    for item in data.problems:
        qid = int(item.get("frontendQuestionId", 0))
        if not qid:
            skipped += 1
            continue

        existing = db.query(Problem).filter(Problem.leetcode_number == qid).first()
        if existing:
            skipped += 1
            continue

        topic_tags = item.get("topicTags", [])
        tag_names = [t.get("name", "") for t in topic_tags]

        difficulty_map = {"Easy": "简单", "Medium": "中等", "Hard": "困难"}
        difficulty = item.get("difficulty", "Medium")
        difficulty_cn = difficulty_map.get(difficulty, difficulty)

        problem = Problem(
            leetcode_number=qid,
            title=item.get("title", ""),
            title_cn=item.get("titleCn", ""),
            leetcode_slug=item.get("titleSlug", ""),
            difficulty=difficulty_cn,
            status="未做",
            topic_tags=str(tag_names) if tag_names else None,
            ac_rate=item.get("acRate"),
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(problem)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


@router.post("/sync-progress")
async def sync_progress(db: Session = Depends(get_db)):
    cookie = db.query(LeetCodeCookie).filter(LeetCodeCookie.is_active == 1).first()
    if not cookie:
        raise HTTPException(status_code=401, detail="未登录 LeetCode")

    try:
        client = LeetCodeClient(cookie=cookie.cookie_value)

        # 获取最近通过的题目
        recent_ac = await client.get_recent_ac_submissions()

        synced = 0
        for submission in recent_ac:
            slug = submission.get("titleSlug", "")
            if not slug:
                continue

            problem = db.query(Problem).filter(Problem.leetcode_slug == slug).first()
            if problem and problem.status == "未做":
                problem.status = "已解"
                problem.last_synced_at = datetime.now(timezone.utc)
                synced += 1

        db.commit()
        return {"synced": synced, "total_ac": len(recent_ac)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
