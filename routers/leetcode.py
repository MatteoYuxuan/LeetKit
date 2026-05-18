from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import SessionLocal
from models import Problem, LeetCodeCookie, Category
from crawler.leetcode_client import LeetCodeClient
from crud import compute_sort_key, sync_problem_categories
from security import encrypt_cookie, decrypt_cookie

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

        # 加密 Cookie 后存储
        encrypted = encrypt_cookie(data.cookie)
        cookie_record = LeetCodeCookie(
            cookie_value=encrypted,
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
):
    try:
        client = LeetCodeClient()
        result = await client.search_problems(
            keyword=q if q else None,
            limit=limit,
            skip=skip,
            difficulty=difficulty,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/problems/{title_slug}/detail")
async def get_problem_detail(title_slug: str):
    try:
        client = LeetCodeClient()
        detail = await client.get_problem_detail(title_slug)
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取题目详情失败: {str(e)}")


@router.post("/import-all")
async def import_all_problems(include_paid: bool = False, db: Session = Depends(get_db)):
    """一键导入所有 LeetCode 算法题目"""
    try:
        client = LeetCodeClient()
        all_problems = await client.fetch_all_problems_with_tags(include_paid=include_paid)

        imported = 0
        updated = 0
        skipped = 0

        for item in all_problems:
            frontend_id = item.get("frontendQuestionId", "")
            if not frontend_id:
                skipped += 1
                continue

            existing = db.query(Problem).filter(Problem.leetcode_number == frontend_id).first()
            if existing:
                # 补充缺失的 slug
                if not existing.leetcode_slug and item.get("titleSlug"):
                    existing.leetcode_slug = item["titleSlug"]
                    updated += 1
                # 补充缺失的中文标题
                if not existing.title_cn and item.get("titleCn"):
                    existing.title_cn = item["titleCn"]
                    updated += 1
                # 修正难度值为大写英文
                if existing.difficulty in ("简单", "中等", "困难"):
                    cn_map = {"简单": "EASY", "中等": "MEDIUM", "困难": "HARD"}
                    existing.difficulty = cn_map.get(existing.difficulty, existing.difficulty)
                    updated += 1
                # 修正排序键
                correct_sort = compute_sort_key(frontend_id)
                if existing.leetcode_number_sort != correct_sort:
                    existing.leetcode_number_sort = correct_sort
                    updated += 1
                # 同步分类
                topic_tag_names = [t["name"] for t in item.get("topicTags", [])]
                if topic_tag_names:
                    sync_problem_categories(db, existing, topic_tag_names)
                skipped += 1
                continue

            difficulty = item.get("difficulty", "MEDIUM").upper()
            if difficulty not in ("EASY", "MEDIUM", "HARD"):
                difficulty = "MEDIUM"

            problem = Problem(
                leetcode_number=frontend_id,
                leetcode_number_sort=compute_sort_key(frontend_id),
                title=item.get("title", ""),
                title_cn=item.get("titleCn", ""),
                leetcode_slug=item.get("titleSlug", ""),
                difficulty=difficulty,
                status="未做",
                ac_rate=item.get("acRate"),
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(problem)

            # 同步分类
            topic_tag_names = [t["name"] for t in item.get("topicTags", [])]
            if topic_tag_names:
                sync_problem_categories(db, problem, topic_tag_names)

            imported += 1

        db.commit()
        return {"imported": imported, "updated": updated, "skipped": skipped, "total": len(all_problems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/sync-titles")
async def sync_chinese_titles(db: Session = Depends(get_db)):
    """批量同步题目的中文标题"""
    try:
        client = LeetCodeClient()
        titles_map = await client.fetch_all_problem_titles()

        problems = db.query(Problem).filter(
            (Problem.title_cn == None) | (Problem.title_cn == "")
        ).all()

        updated = 0
        for p in problems:
            fid = str(p.leetcode_number)
            if fid in titles_map:
                p.title_cn = titles_map[fid]
                updated += 1

        db.commit()
        return {"updated": updated, "total": len(problems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/import")
def import_problems(data: ImportRequest, db: Session = Depends(get_db)):
    imported = 0
    skipped = 0
    for item in data.problems:
        qid = item.get("frontendQuestionId", "")
        if not qid:
            skipped += 1
            continue

        existing = db.query(Problem).filter(Problem.leetcode_number == qid).first()
        if existing:
            skipped += 1
            continue

        topic_tags = item.get("topicTags", [])
        tag_names = [t.get("name", "") for t in topic_tags]

        difficulty = item.get("difficulty", "MEDIUM").upper()
        if difficulty not in ("EASY", "MEDIUM", "HARD"):
            difficulty = "MEDIUM"

        problem = Problem(
            leetcode_number=qid,
            leetcode_number_sort=compute_sort_key(qid),
            title=item.get("title", ""),
            title_cn=item.get("titleCn", ""),
            leetcode_slug=item.get("titleSlug", ""),
            difficulty=difficulty,
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
        # 解密 Cookie（兼容旧的明文数据）
        try:
            cookie_value = decrypt_cookie(cookie.cookie_value)
        except Exception:
            cookie_value = cookie.cookie_value

        client = LeetCodeClient(cookie=cookie_value)

        # 先验证 cookie 并获取用户名
        user_info = await client.verify_cookie()
        if not user_info["is_signed_in"]:
            raise HTTPException(status_code=401, detail="Cookie 已过期，请重新登录")

        username = user_info["username"]

        # 获取用户已解决的题目
        solved_problems = await client.get_user_solved_problems(username, limit=500)

        synced = 0
        for question in solved_problems:
            slug = question.get("titleSlug", "")
            if not slug:
                continue

            problem = db.query(Problem).filter(Problem.leetcode_slug == slug).first()
            if problem and problem.status == "未做":
                problem.status = "已解"
                problem.last_synced_at = datetime.now(timezone.utc)
                synced += 1

        db.commit()
        return {"synced": synced, "total_solved": len(solved_problems), "username": username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/fix-sort-keys")
def fix_sort_keys(db: Session = Depends(get_db)):
    """修正所有题目的排序键"""
    problems = db.query(Problem).all()
    updated = 0
    for p in problems:
        correct = compute_sort_key(p.leetcode_number)
        if p.leetcode_number_sort != correct:
            p.leetcode_number_sort = correct
            updated += 1
    db.commit()
    return {"updated": updated, "total": len(problems)}


@router.post("/sync-categories")
async def sync_categories(db: Session = Depends(get_db)):
    """为已有题目补全分类（从 LeetCode topicTags 映射）"""
    try:
        client = LeetCodeClient()
        all_problems = await client.fetch_all_problems_with_tags()

        # 构建 frontendQuestionId -> topicTags 的映射
        id_to_tags = {}
        for item in all_problems:
            fid = item.get("frontendQuestionId", "")
            tag_names = [t["name"] for t in item.get("topicTags", [])]
            if fid and tag_names:
                id_to_tags[fid] = tag_names

        # 获取所有没有分类的题目
        problems = db.query(Problem).all()
        updated = 0

        for p in problems:
            tag_names = id_to_tags.get(p.leetcode_number, [])
            if tag_names:
                old_count = len(p.categories)
                sync_problem_categories(db, p, tag_names)
                if len(p.categories) > old_count:
                    updated += 1

        db.commit()
        return {"updated": updated, "total": len(problems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步分类失败: {str(e)}")
