import re
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, or_, select, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from models import Problem, Category, Tag, Note, ReviewRecord, ReviewSchedule, problem_tags, note_tags, problem_categories, note_categories
import schemas


# --- LeetCode topicTags 到分类的映射 ---

TOPIC_TAG_TO_CATEGORY = {
    "Array": "数组",
    "String": "字符串",
    "Hash Table": "哈希表",
    "Linked List": "链表",
    "Stack": "栈",
    "Queue": "队列",
    "Binary Tree": "二叉树",
    "Tree": "二叉树",
    "Graph": "图",
    "Dynamic Programming": "动态规划",
    "Greedy": "贪心",
    "Binary Search": "二分查找",
    "Backtracking": "回溯",
    "Sorting": "排序",
    "Two Pointers": "双指针",
    "Sliding Window": "滑动窗口",
    "Bit Manipulation": "位运算",
    "Math": "数学",
    "Design": "设计",
    "Heap (Priority Queue)": "堆",
    "Union Find": "并查集",
    "Trie": "字典树",
    "Divide and Conquer": "分治",
    "Recursion": "递归",
    "Memoization": "记忆化",
    "Depth-First Search": "深度优先搜索",
    "Breadth-First Search": "广度优先搜索",
    "Binary Indexed Tree": "树状数组",
    "Segment Tree": "线段树",
}


def sync_problem_categories(db: Session, problem: Problem, topic_tag_names: list[str]):
    """从 LeetCode topicTags 自动关联分类"""
    for name in topic_tag_names:
        cat_name = TOPIC_TAG_TO_CATEGORY.get(name)
        if cat_name:
            cat = db.query(Category).filter(Category.name == cat_name).first()
            if not cat:
                cat = Category(name=cat_name)
                db.add(cat)
                db.flush()  # 确保后续查询能查到新分类，避免重复插入
            if cat not in problem.categories:
                problem.categories.append(cat)


# --- Sort key computation ---

_PREFIX_ORDER = {
    "LCP": 1_000_000,
    "LCR": 2_000_000,
    "LCS": 3_000_000,
    "LCOF": 4_000_000,
    "LCOF2": 5_000_000,
}


def compute_sort_key(frontend_id: str) -> int:
    """Compute a numeric sort key from frontendQuestionId.
    Pure numbers sort numerically; prefixed IDs (LCP, LCR, etc.) sort after
    all regular numbers, grouped by prefix then by suffix number."""
    s = frontend_id.strip()
    if s.isdigit():
        return int(s)
    # 先尝试匹配已知前缀（包括 LCOF2 等含数字的前缀）
    for prefix in sorted(_PREFIX_ORDER.keys(), key=len, reverse=True):
        if s.upper().startswith(prefix):
            rest = s[len(prefix):].strip()
            if rest.isdigit():
                return _PREFIX_ORDER[prefix] + int(rest)
    # 通用模式：字母前缀 + 数字
    m = re.match(r"^([A-Za-z]+)\s*(\d+)$", s)
    if m:
        prefix = m.group(1).upper()
        num = int(m.group(2))
        offset = _PREFIX_ORDER.get(prefix, 9_000_000)
        return offset + num
    return 9_999_999


# --- Category CRUD ---

def get_categories(db: Session) -> list[dict]:
    # Count problems + notes per category via junction tables
    all_refs = (
        select(problem_categories.c.category_id.label("cat_id"))
        .union_all(select(note_categories.c.category_id.label("cat_id")))
    ).subquery()
    stmt = (
        select(Category, func.count(all_refs.c.cat_id).label("problem_count"))
        .outerjoin(all_refs, all_refs.c.cat_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name)
    )
    rows = db.execute(stmt).all()
    result = []
    for cat, count in rows:
        d = {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color": cat.color,
            "problem_count": count,
        }
        result.append(d)
    return result


def create_category(db: Session, data: schemas.CategoryCreate) -> Category:
    cat = Category(**data.model_dump())
    db.add(cat)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(cat)
    return cat


def update_category(db: Session, cat_id: int, data: schemas.CategoryUpdate) -> Category | None:
    cat = db.get(Category, cat_id)
    if not cat:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, cat_id: int) -> bool:
    cat = db.get(Category, cat_id)
    if not cat:
        return False
    has_problems = db.scalar(select(func.count(problem_categories.c.problem_id)).where(problem_categories.c.category_id == cat_id))
    has_notes = db.scalar(select(func.count(note_categories.c.note_id)).where(note_categories.c.category_id == cat_id))
    if has_problems or has_notes:
        return False
    db.delete(cat)
    db.commit()
    return True


# --- Tag CRUD ---

def get_tags(db: Session) -> list[dict]:
    # Count both problems and notes per tag
    prob_counts = (
        select(problem_tags.c.tag_id.label("tag_id"))
        .union_all(select(note_tags.c.tag_id.label("tag_id")))
    ).subquery()
    stmt = (
        select(Tag, func.count(prob_counts.c.tag_id).label("problem_count"))
        .outerjoin(prob_counts, prob_counts.c.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    rows = db.execute(stmt).all()
    result = []
    for tag, count in rows:
        d = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "problem_count": count,
        }
        result.append(d)
    return result


def create_tag(db: Session, data: schemas.TagCreate) -> Tag:
    tag = Tag(**data.model_dump())
    db.add(tag)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(tag)
    return tag


def update_tag(db: Session, tag_id: int, data: schemas.TagUpdate) -> Tag | None:
    tag = db.get(Tag, tag_id)
    if not tag:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> bool:
    tag = db.get(Tag, tag_id)
    if not tag:
        return False
    db.delete(tag)
    db.commit()
    return True


# --- Shared helpers ---

_ALLOWED_SORT_FIELDS = {
    "leetcode_number", "title", "title_cn", "difficulty",
    "status", "created_at", "ac_rate", "page_number",
}


def _sync_tags_and_categories(db: Session, entity, tag_ids: list[int] | None, category_ids: list[int] | None):
    """统一设置实体的标签和分类关联"""
    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
        entity.tags = tags
    if category_ids is not None:
        cats = db.query(Category).filter(Category.id.in_(category_ids)).all() if category_ids else []
        entity.categories = cats


def _calc_streak_from_dates(all_dates: list[str], today_str: str) -> tuple[int, int]:
    """统一计算连续天数和最长连续天数，返回 (streak, longest_streak)"""
    dates_set = set(all_dates)
    streak = 0
    d = datetime.strptime(today_str, "%Y-%m-%d")
    while d.strftime("%Y-%m-%d") in dates_set:
        streak += 1
        d -= timedelta(days=1)

    if not all_dates:
        return streak, 0
    parsed = sorted(datetime.strptime(dd, "%Y-%m-%d") for dd in all_dates)
    longest = 1
    current = 1
    for i in range(1, len(parsed)):
        if (parsed[i] - parsed[i - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return streak, max(longest, current)


# --- Problem CRUD ---

def get_problems(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    difficulty: str | None = None,
    status: str | None = None,
    category_id: int | None = None,
    tag_id: int | None = None,
    q: str | None = None,
    sort_by: str = "leetcode_number",
    sort_order: str = "asc",
) -> tuple[list[Problem], int]:
    stmt = select(Problem).options(joinedload(Problem.categories), joinedload(Problem.tags))
    count_stmt = select(func.count(Problem.id))

    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)
        count_stmt = count_stmt.where(Problem.difficulty == difficulty)
    if status:
        stmt = stmt.where(Problem.status == status)
        count_stmt = count_stmt.where(Problem.status == status)
    if category_id:
        cat_sub = select(problem_categories.c.problem_id).where(problem_categories.c.category_id == category_id)
        stmt = stmt.where(Problem.id.in_(cat_sub))
        count_stmt = count_stmt.where(Problem.id.in_(cat_sub))
    if tag_id:
        tag_sub = select(problem_tags.c.problem_id).where(problem_tags.c.tag_id == tag_id)
        stmt = stmt.where(Problem.id.in_(tag_sub))
        count_stmt = count_stmt.where(Problem.id.in_(tag_sub))
    if q:
        escaped_q = q.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_q}%"
        search_filter = or_(
            Problem.title.ilike(pattern),
            Problem.title_cn.ilike(pattern),
            Problem.notes.ilike(pattern),
            Problem.leetcode_number.ilike(pattern),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.scalar(count_stmt) or 0

    if sort_by not in _ALLOWED_SORT_FIELDS:
        sort_by = "leetcode_number"
    if sort_by == "leetcode_number":
        sort_column = Problem.leetcode_number_sort
    else:
        sort_column = getattr(Problem, sort_by, Problem.leetcode_number_sort)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    problems = db.execute(stmt).unique().scalars().all()
    return problems, total


def get_problem(db: Session, problem_id: int) -> Problem | None:
    stmt = select(Problem).options(joinedload(Problem.categories), joinedload(Problem.tags)).where(Problem.id == problem_id)
    return db.execute(stmt).unique().scalar_one_or_none()


def create_problem(db: Session, data: schemas.ProblemCreate) -> Problem:
    tag_ids = data.tag_ids
    category_ids = data.category_ids
    problem_data = data.model_dump(exclude={"tag_ids", "category_ids"})
    if "leetcode_number_sort" not in problem_data or not problem_data["leetcode_number_sort"]:
        problem_data["leetcode_number_sort"] = compute_sort_key(problem_data["leetcode_number"])
    problem = Problem(**problem_data)
    if problem.status == "已解" and not problem.solved_at:
        problem.solved_at = datetime.now(timezone.utc)
    _sync_tags_and_categories(db, problem, tag_ids, category_ids)
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


def update_problem(db: Session, problem_id: int, data: schemas.ProblemUpdate) -> Problem | None:
    problem = db.get(Problem, problem_id)
    if not problem:
        return None
    update_data = data.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)
    category_ids = update_data.pop("category_ids", None)
    for key, value in update_data.items():
        setattr(problem, key, value)
    _sync_tags_and_categories(db, problem, tag_ids, category_ids)
    if problem.status == "已解" and not problem.solved_at:
        problem.solved_at = datetime.now(timezone.utc)
    problem.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(problem)
    return problem


def delete_problem(db: Session, problem_id: int) -> bool:
    problem = db.get(Problem, problem_id)
    if not problem:
        return False
    db.delete(problem)
    db.commit()
    return True


# --- Note CRUD ---

def get_notes(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category_id: int | None = None,
    tag_id: int | None = None,
    q: str | None = None,
) -> tuple[list[Note], int]:
    stmt = select(Note).options(joinedload(Note.categories), joinedload(Note.tags))
    count_stmt = select(func.count(Note.id))

    if category_id:
        cat_sub = select(note_categories.c.note_id).where(note_categories.c.category_id == category_id)
        stmt = stmt.where(Note.id.in_(cat_sub))
        count_stmt = count_stmt.where(Note.id.in_(cat_sub))
    if tag_id:
        tag_sub = select(note_tags.c.note_id).where(note_tags.c.tag_id == tag_id)
        stmt = stmt.where(Note.id.in_(tag_sub))
        count_stmt = count_stmt.where(Note.id.in_(tag_sub))
    if q:
        escaped_q = q.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_q}%"
        search_filter = or_(Note.title.ilike(pattern), Note.content.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Note.updated_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    notes = db.execute(stmt).unique().scalars().all()
    return notes, total


def get_note(db: Session, note_id: int) -> Note | None:
    stmt = select(Note).options(joinedload(Note.categories), joinedload(Note.tags)).where(Note.id == note_id)
    return db.execute(stmt).unique().scalar_one_or_none()


def create_note(db: Session, data: schemas.NoteCreate) -> Note:
    tag_ids = data.tag_ids
    category_ids = data.category_ids
    note_data = data.model_dump(exclude={"tag_ids", "category_ids"})
    note = Note(**note_data)
    _sync_tags_and_categories(db, note, tag_ids, category_ids)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, note_id: int, data: schemas.NoteUpdate) -> Note | None:
    note = db.get(Note, note_id)
    if not note:
        return None
    update_data = data.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)
    category_ids = update_data.pop("category_ids", None)
    for key, value in update_data.items():
        setattr(note, key, value)
    _sync_tags_and_categories(db, note, tag_ids, category_ids)
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int) -> bool:
    note = db.get(Note, note_id)
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


# --- Stats ---

def get_stats_overview(db: Session) -> dict:
    total = db.scalar(select(func.count(Problem.id))) or 0
    note_total = db.scalar(select(func.count(Note.id))) or 0

    status_rows = db.execute(
        select(Problem.status, func.count(Problem.id)).group_by(Problem.status)
    ).all()
    by_status = {row[0]: row[1] for row in status_rows}

    diff_rows = db.execute(
        select(
            Problem.difficulty,
            func.count(Problem.id).label("total"),
            func.sum(case((Problem.status == "已解", 1), else_=0)).label("solved"),
        ).group_by(Problem.difficulty)
    ).all()
    by_difficulty = {diff: {"total": cnt, "已解": int(solved or 0)} for diff, cnt, solved in diff_rows}

    return {"total": total, "note_total": note_total, "by_status": by_status, "by_difficulty": by_difficulty}


def get_stats_by_category(db: Session) -> list[dict]:
    stmt = (
        select(
            Category.name,
            func.count(problem_categories.c.problem_id).label("count"),
            func.sum(case((Problem.status == "已解", 1), else_=0)).label("solved"),
        )
        .outerjoin(problem_categories, problem_categories.c.category_id == Category.id)
        .outerjoin(Problem, Problem.id == problem_categories.c.problem_id)
        .group_by(Category.id)
        .order_by(func.count(problem_categories.c.problem_id).desc())
    )
    rows = db.execute(stmt).all()
    return [{"name": row[0], "count": row[1], "solved": int(row[2] or 0)} for row in rows if row[1] > 0]


def get_stats_by_difficulty(db: Session) -> list[dict]:
    stmt = (
        select(Problem.difficulty, Problem.status, func.count(Problem.id))
        .group_by(Problem.difficulty, Problem.status)
    )
    rows = db.execute(stmt).all()
    result = {}
    for diff, status, count in rows:
        if diff not in result:
            result[diff] = {}
        result[diff][status] = count
    return result


def get_stats_progress(db: Session) -> list[dict]:
    stmt = (
        select(
            func.strftime("%Y-%m", Problem.solved_at).label("month"),
            func.count(Problem.id).label("count"),
        )
        .where(Problem.status == "已解", Problem.solved_at.is_not(None))
        .group_by("month")
        .order_by("month")
    )
    rows = db.execute(stmt).all()
    cumulative = 0
    result = []
    for month, count in rows:
        cumulative += count
        result.append({"month": month, "count": count, "cumulative_solved": cumulative})
    return result


def get_stats_recent(db: Session, limit: int = 10) -> list[Problem]:
    stmt = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags))
        .order_by(Problem.updated_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).unique().scalars().all()


def reset_solved_at(db: Session) -> dict:
    """清空所有题目的 solved_at，重置解题趋势"""
    count = db.query(Problem).filter(Problem.solved_at.is_not(None)).update({Problem.solved_at: None})
    db.commit()
    return {"reset": count}


def get_stats_heatmap(db: Session, year: int = None) -> dict:
    """获取热力图数据：签到日期集合"""
    from datetime import datetime
    if year is None:
        year = datetime.now().year
    dates = get_checkin_dates(db, year)
    return {"year": year, "dates": dates}


# --- Review (艾宾浩斯遗忘曲线) ---

# 艾宾浩斯复习间隔（天）
EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

# 旧系统兼容
BASE_INTERVAL = {"EASY": 3, "MEDIUM": 2, "HARD": 1}
MULTIPLIER = {0: None, 1: 1.2, 2: 2.5, 3: 4.0}
DIFFICULTY_FACTOR = {"EASY": 1.3, "MEDIUM": 1.0, "HARD": 0.7}


def _now():
    """Naive UTC datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_next_review(db: Session, daily_limit: int = 3, exclude_id: int | None = None, problem_ids: list[int] | None = None) -> Problem | None:
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Count today's completed reviews
    completed_today = db.scalar(
        select(func.count(ReviewRecord.id)).where(ReviewRecord.created_at >= today_start)
    ) or 0
    if completed_today >= daily_limit:
        return None

    # 优先级 1: 需复盘状态的题目（按 updated_at, id 排序保证确定性）
    review_query = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags))
        .where(Problem.status == "需复盘")
        .order_by(Problem.updated_at.asc(), Problem.id.asc())
    )
    if exclude_id is not None:
        review_query = review_query.where(Problem.id != exclude_id)
    if problem_ids is not None:
        review_query = review_query.where(Problem.id.in_(problem_ids))
    result = db.execute(review_query).unique().scalars().first()
    if result:
        return result

    # 优先级 2: 艾宾浩斯计划中到期的题目
    overdue_query = (
        select(ReviewSchedule)
        .options(joinedload(ReviewSchedule.problem))
        .where(
            ReviewSchedule.is_completed == 0,
            ReviewSchedule.next_review_at <= now,
        )
        .order_by(ReviewSchedule.next_review_at.asc(), ReviewSchedule.id.asc())
    )
    if exclude_id is not None:
        overdue_query = overdue_query.where(ReviewSchedule.problem_id != exclude_id)
    if problem_ids is not None:
        overdue_query = overdue_query.where(ReviewSchedule.problem_id.in_(problem_ids))
    schedule = db.execute(overdue_query).scalars().first()
    if schedule and schedule.problem:
        problem = schedule.problem
        db.refresh(problem)
        return problem

    # 优先级 3: 已解但从未加入复习计划的题目
    scheduled_ids = select(ReviewSchedule.problem_id).where(ReviewSchedule.is_completed == 0)
    never_query = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags))
        .where(Problem.status == "已解", ~Problem.id.in_(scheduled_ids))
        .order_by(Problem.updated_at.asc(), Problem.id.asc())
    )
    if exclude_id is not None:
        never_query = never_query.where(Problem.id != exclude_id)
    if problem_ids is not None:
        never_query = never_query.where(Problem.id.in_(problem_ids))
    result = db.execute(never_query).unique().scalars().first()
    if result:
        return result

    return None


def create_review_schedule(db: Session, problem_id: int) -> ReviewSchedule:
    """为题目创建艾宾浩斯复习计划"""
    now = _now()
    schedule = ReviewSchedule(
        problem_id=problem_id,
        stage=0,
        next_review_at=now + timedelta(days=EBBINGHAUS_INTERVALS[0]),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def submit_review(db: Session, problem_id: int, rating: int, time_spent: int | None = None) -> ReviewRecord:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise ValueError("题目不存在")

    now = _now()

    # 获取或创建艾宾浩斯复习计划
    schedule = db.query(ReviewSchedule).filter(
        ReviewSchedule.problem_id == problem_id,
        ReviewSchedule.is_completed == 0,
    ).first()

    if not schedule:
        schedule = create_review_schedule(db, problem_id)

    # 根据评分决定下一个复习阶段
    if rating >= 2:
        # 掌握良好，进入下一阶段
        next_stage = schedule.stage + 1
        if next_stage >= len(EBBINGHAUS_INTERVALS):
            # 完成所有复习阶段
            schedule.is_completed = 1
            schedule.stage = next_stage
            schedule.next_review_at = now
            new_interval = EBBINGHAUS_INTERVALS[-1]
        else:
            schedule.stage = next_stage
            new_interval = EBBINGHAUS_INTERVALS[next_stage]
            schedule.next_review_at = now + timedelta(days=new_interval)
    elif rating == 1:
        # 模糊，保持当前阶段，缩短间隔
        new_interval = max(1, EBBINGHAUS_INTERVALS[schedule.stage] // 2)
        schedule.next_review_at = now + timedelta(days=new_interval)
    else:
        # 完全不会，重置到第一阶段
        schedule.stage = 0
        new_interval = EBBINGHAUS_INTERVALS[0]
        schedule.next_review_at = now + timedelta(days=new_interval)

    # 记录复习历史
    record = ReviewRecord(
        problem_id=problem_id,
        rating=rating,
        interval=new_interval,
        time_spent=time_spent,
    )
    db.add(record)

    # 更新题目状态
    if rating >= 2 and problem.status == "需复盘":
        problem.status = "已解"
        problem.solved_at = now
    elif rating == 0:
        problem.status = "需复盘"

    problem.updated_at = now
    db.commit()
    db.refresh(record)
    return record


def get_review_stats(db: Session) -> dict:
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    completed_today = db.scalar(
        select(func.count(ReviewRecord.id)).where(ReviewRecord.created_at >= today_start)
    ) or 0
    total_reviews = db.scalar(select(func.count(ReviewRecord.id))) or 0

    # 待复习数量
    pending = 0

    # 需复盘状态
    pending += db.scalar(select(func.count(Problem.id)).where(Problem.status == "需复盘")) or 0

    # 艾宾浩斯计划中到期的
    pending += db.scalar(
        select(func.count(ReviewSchedule.id)).where(
            ReviewSchedule.is_completed == 0,
            ReviewSchedule.next_review_at <= now,
        )
    ) or 0

    # 已解但未加入计划的
    scheduled_ids = select(ReviewSchedule.problem_id).where(ReviewSchedule.is_completed == 0)
    pending += db.scalar(
        select(func.count(Problem.id)).where(
            Problem.status == "已解",
            ~Problem.id.in_(scheduled_ids),
        )
    ) or 0

    return {"pending": pending, "completed_today": completed_today, "total_reviews": total_reviews}


def get_today_reviews(db: Session) -> list[dict]:
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    records = (
        db.query(ReviewRecord)
        .options(joinedload(ReviewRecord.problem))
        .filter(ReviewRecord.created_at >= today_start)
        .order_by(ReviewRecord.created_at.desc())
        .all()
    )
    result = []
    for r in records:
        next_at = r.created_at + timedelta(days=r.interval)
        result.append({
            "id": r.id,
            "problem_id": r.problem_id,
            "leetcode_number": r.problem.leetcode_number,
            "leetcode_slug": r.problem.leetcode_slug,
            "title": r.problem.title,
            "title_cn": r.problem.title_cn,
            "rating": r.rating,
            "interval": r.interval,
            "time_spent": r.time_spent,
            "next_review_at": next_at.isoformat(),
        })
    return result


def get_review_timeline(db: Session) -> list[dict]:
    """获取艾宾浩斯复习时间线"""
    now = _now()
    schedules = (
        db.query(ReviewSchedule)
        .options(joinedload(ReviewSchedule.problem))
        .filter(ReviewSchedule.is_completed == 0)
        .order_by(ReviewSchedule.next_review_at.asc())
        .all()
    )
    result = []
    for s in schedules:
        result.append({
            "id": s.id,
            "problem_id": s.problem_id,
            "leetcode_number": s.problem.leetcode_number if s.problem else None,
            "leetcode_slug": s.problem.leetcode_slug if s.problem else None,
            "title": s.problem.title if s.problem else None,
            "title_cn": s.problem.title_cn if s.problem else None,
            "stage": s.stage,
            "total_stages": len(EBBINGHAUS_INTERVALS),
            "next_review_at": s.next_review_at.isoformat(),
            "is_overdue": s.next_review_at <= now,
        })
    return result


# --- Daily Check-in ---

def checkin_today(db: Session) -> dict:
    """记录今天签到，返回签到统计"""
    from models import DailyCheckin
    now = datetime.now()  # 本地时间
    today_str = now.strftime("%Y-%m-%d")

    existing = db.query(DailyCheckin).filter(DailyCheckin.date == today_str).first()
    is_first = not existing

    if is_first:
        try:
            db.add(DailyCheckin(date=today_str))
            db.commit()
        except IntegrityError:
            db.rollback()
            is_first = False

    # Calculate streak
    all_dates = sorted(
        [row[0] for row in db.execute(
            select(DailyCheckin.date).order_by(DailyCheckin.date.desc())
        ).all()]
    )

    streak, longest = _calc_streak_from_dates(all_dates, today_str)
    total = len(all_dates)

    return {
        "is_first_today": is_first,
        "streak": streak,
        "longest_streak": longest,
        "total_checkins": total,
    }


def get_checkin_stats(db: Session) -> dict:
    """获取签到统计"""
    from models import DailyCheckin
    now = datetime.now()  # 本地时间
    today_str = now.strftime("%Y-%m-%d")

    existing = db.query(DailyCheckin).filter(DailyCheckin.date == today_str).first()
    all_dates = sorted(
        [row[0] for row in db.execute(
            select(DailyCheckin.date).order_by(DailyCheckin.date.desc())
        ).all()]
    )

    streak, longest = _calc_streak_from_dates(all_dates, today_str)

    return {
        "checked_in_today": existing is not None,
        "streak": streak,
        "longest_streak": longest,
        "total_checkins": len(all_dates),
    }


def get_checkin_dates(db: Session, year: int) -> list[str]:
    """获取指定年份所有签到日期"""
    from models import DailyCheckin
    rows = db.execute(
        select(DailyCheckin.date).where(
            DailyCheckin.date >= f"{year}-01-01",
            DailyCheckin.date <= f"{year}-12-31",
        )
    ).all()
    return [row[0] for row in rows]
