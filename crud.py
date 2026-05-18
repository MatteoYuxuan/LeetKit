from datetime import datetime, timezone, timedelta
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from models import Problem, Category, Tag, Note, ReviewRecord, problem_tags, note_tags, problem_categories, note_categories
import schemas


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
    db.commit()
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
    if cat.problems or cat.notes:
        return False
    db.delete(cat)
    db.commit()
    return True


# --- Tag CRUD ---

def get_tags(db: Session) -> list[dict]:
    from sqlalchemy import union_all
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
    db.commit()
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
        pattern = f"%{q}%"
        search_filter = or_(
            Problem.title.ilike(pattern),
            Problem.title_cn.ilike(pattern),
            Problem.notes.ilike(pattern),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.scalar(count_stmt) or 0

    sort_column = getattr(Problem, sort_by, Problem.leetcode_number)
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
    problem = Problem(**problem_data)
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        problem.tags = tags
    if category_ids:
        cats = db.query(Category).filter(Category.id.in_(category_ids)).all()
        problem.categories = cats
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
    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        problem.tags = tags
    if category_ids is not None:
        cats = db.query(Category).filter(Category.id.in_(category_ids)).all()
        problem.categories = cats
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
        pattern = f"%{q}%"
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
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        note.tags = tags
    if category_ids:
        cats = db.query(Category).filter(Category.id.in_(category_ids)).all()
        note.categories = cats
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
    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        note.tags = tags
    if category_ids is not None:
        cats = db.query(Category).filter(Category.id.in_(category_ids)).all()
        note.categories = cats
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
        select(Problem.difficulty, func.count(Problem.id)).group_by(Problem.difficulty)
    ).all()
    by_difficulty = {}
    for diff, cnt in diff_rows:
        solved = db.scalar(
            select(func.count(Problem.id)).where(
                Problem.difficulty == diff, Problem.status == "已解"
            )
        ) or 0
        by_difficulty[diff] = {"total": cnt, "已解": solved}

    return {"total": total, "note_total": note_total, "by_status": by_status, "by_difficulty": by_difficulty}


def get_stats_by_category(db: Session) -> list[dict]:
    stmt = (
        select(Category.name, func.count(problem_categories.c.problem_id).label("count"))
        .outerjoin(problem_categories, problem_categories.c.category_id == Category.id)
        .group_by(Category.id)
        .order_by(func.count(problem_categories.c.problem_id).desc())
    )
    rows = db.execute(stmt).all()
    return [{"name": row[0], "count": row[1]} for row in rows if row[1] > 0]


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
            func.strftime("%Y-W%W", Problem.updated_at).label("week"),
            func.count(Problem.id).label("count"),
        )
        .where(Problem.status == "已解")
        .group_by("week")
        .order_by("week")
    )
    rows = db.execute(stmt).all()
    cumulative = 0
    result = []
    for week, count in rows:
        cumulative += count
        result.append({"week": week, "cumulative_solved": cumulative})
    return result


def get_stats_recent(db: Session, limit: int = 10) -> list[Problem]:
    stmt = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags))
        .order_by(Problem.updated_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).unique().scalars().all()


# --- Review ---

BASE_INTERVAL = {"EASY": 3, "MEDIUM": 2, "HARD": 1}
MULTIPLIER = {0: None, 1: 1.2, 2: 2.5, 3: 4.0}
DIFFICULTY_FACTOR = {"EASY": 1.3, "MEDIUM": 1.0, "HARD": 0.7}


def _now():
    """Naive UTC datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_next_review(db: Session, daily_limit: int = 10) -> Problem | None:
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Count today's completed reviews
    completed_today = db.scalar(
        select(func.count(ReviewRecord.id)).where(ReviewRecord.created_at >= today_start)
    ) or 0
    if completed_today >= daily_limit:
        return None

    # Subquery: latest review per problem
    latest_review = (
        select(
            ReviewRecord.problem_id,
            func.max(ReviewRecord.id).label("max_id"),
        )
        .group_by(ReviewRecord.problem_id)
        .subquery()
    )

    # Priority 1: "需复盘" problems (ordered by updated_at)
    review_problems = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags), joinedload(Problem.reviews))
        .where(Problem.status == "需复盘")
        .order_by(Problem.updated_at.asc())
    )
    result = db.execute(review_problems).unique().scalars().first()
    if result:
        return result

    # Priority 2: overdue reviews — fetch candidates and filter in Python
    # (SQLite doesn't support datetime arithmetic)
    reviewed_ids = select(latest_review.c.problem_id)
    candidates = (
        db.execute(
            select(Problem)
            .options(joinedload(Problem.categories), joinedload(Problem.tags), joinedload(Problem.reviews))
            .where(Problem.status == "已解", Problem.id.in_(reviewed_ids))
            .order_by(Problem.updated_at.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    overdue = []
    for p in candidates:
        if p.reviews:
            latest = max(p.reviews, key=lambda r: r.id)
            next_at = latest.created_at + timedelta(days=latest.interval)
            if next_at <= now:
                overdue.append((next_at, p))
    if overdue:
        overdue.sort(key=lambda x: x[0])
        return overdue[0][1]

    # Priority 3: "已解" problems never reviewed
    never_reviewed = (
        select(Problem)
        .options(joinedload(Problem.categories), joinedload(Problem.tags), joinedload(Problem.reviews))
        .where(Problem.status == "已解", ~Problem.id.in_(reviewed_ids))
        .order_by(Problem.updated_at.asc())
    )
    result = db.execute(never_reviewed).unique().scalars().first()
    if result:
        return result

    return None


def submit_review(db: Session, problem_id: int, rating: int) -> ReviewRecord:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise ValueError("题目不存在")

    # Get the latest review record
    latest = (
        db.query(ReviewRecord)
        .filter(ReviewRecord.problem_id == problem_id)
        .order_by(ReviewRecord.created_at.desc())
        .first()
    )

    if rating == 0:
        new_interval = BASE_INTERVAL.get(problem.difficulty, 2)
    else:
        prev_interval = latest.interval if latest else BASE_INTERVAL.get(problem.difficulty, 2)
        new_interval = max(1, round(prev_interval * MULTIPLIER[rating]))

    # Apply difficulty factor
    new_interval = max(1, round(new_interval * DIFFICULTY_FACTOR.get(problem.difficulty, 1.0)))

    record = ReviewRecord(
        problem_id=problem_id,
        rating=rating,
        interval=new_interval,
    )
    db.add(record)

    # Auto-update status: if rating >= 2 and status is "需复盘", change to "已解"
    if rating >= 2 and problem.status == "需复盘":
        problem.status = "已解"

    problem.updated_at = _now()
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

    # Pending count
    pending = 0

    # "需复盘" count
    pending += db.scalar(select(func.count(Problem.id)).where(Problem.status == "需复盘")) or 0

    # Overdue: "已解" with latest review's next_review_at <= now
    latest_review = (
        select(ReviewRecord.problem_id, func.max(ReviewRecord.id).label("max_id"))
        .group_by(ReviewRecord.problem_id)
        .subquery()
    )
    reviewed_ids = select(latest_review.c.problem_id)
    # Fetch reviewed "已解" problems and filter overdue in Python
    reviewed_problems = db.execute(
        select(Problem.id)
        .where(Problem.status == "已解", Problem.id.in_(reviewed_ids))
    ).scalars().all()
    if reviewed_problems:
        latest_records = db.execute(
            select(ReviewRecord)
            .join(latest_review, ReviewRecord.id == latest_review.c.max_id)
            .where(ReviewRecord.problem_id.in_(reviewed_problems))
        ).scalars().all()
        for r in latest_records:
            next_at = r.created_at + timedelta(days=r.interval)
            if next_at <= now:
                pending += 1

    # Never reviewed "已解"
    never_reviewed = db.scalar(
        select(func.count(Problem.id))
        .where(Problem.status == "已解", ~Problem.id.in_(reviewed_ids))
    ) or 0
    pending += never_reviewed

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
            "title": r.problem.title,
            "rating": r.rating,
            "interval": r.interval,
            "next_review_at": next_at.isoformat(),
        })
    return result
