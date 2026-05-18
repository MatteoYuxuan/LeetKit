"""crud.py 核心逻辑测试"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Problem, Category, Tag, ReviewRecord, ReviewSchedule
from crud import (
    compute_sort_key,
    create_problem,
    get_problems,
    submit_review,
    create_review_schedule,
    get_next_review,
    EBBINGHAUS_INTERVALS,
)


@pytest.fixture
def db():
    """创建内存数据库用于测试"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ========== 排序键测试 ==========

class TestComputeSortKey:
    def test_regular_number(self):
        assert compute_sort_key("1") == 1
        assert compute_sort_key("100") == 100
        assert compute_sort_key("2999") == 2999

    def test_lcp_prefix(self):
        assert compute_sort_key("LCP 1") == 1_000_001
        assert compute_sort_key("LCP 100") == 1_000_100

    def test_lcr_prefix(self):
        assert compute_sort_key("LCR 1") == 2_000_001

    def test_lcs_prefix(self):
        assert compute_sort_key("LCS 1") == 3_000_001

    def test_lcof_prefix(self):
        assert compute_sort_key("LCOF 1") == 4_000_001

    def test_lcof2_prefix(self):
        assert compute_sort_key("LCOF2 1") == 5_000_001

    def test_unknown_prefix(self):
        assert compute_sort_key("UNKNOWN 1") == 9_000_001

    def test_sort_order(self):
        """确保排序顺序正确: 数字 < LCP < LCR < LCS < LCOF < LCOF2 < 其他"""
        keys = [
            compute_sort_key("1"),
            compute_sort_key("LCP 1"),
            compute_sort_key("LCR 1"),
            compute_sort_key("LCS 1"),
            compute_sort_key("LCOF 1"),
            compute_sort_key("LCOF2 1"),
        ]
        assert keys == sorted(keys)

    def test_whitespace_handling(self):
        assert compute_sort_key(" 1 ") == 1
        assert compute_sort_key(" LCP 1 ") == 1_000_001


# ========== 题目 CRUD 测试 ==========

class TestProblemCRUD:
    def test_create_problem(self, db):
        data = type("ProblemCreate", (), {
            "leetcode_number": "1",
            "title": "Two Sum",
            "title_cn": "两数之和",
            "leetcode_slug": "two-sum",
            "page_number": None,
            "difficulty": "EASY",
            "status": "未做",
            "category_ids": [],
            "notes": None,
            "solution_url": None,
            "time_complexity": None,
            "space_complexity": None,
            "tag_ids": [],
            "model_dump": lambda self, **kwargs: {
                "leetcode_number": "1",
                "title": "Two Sum",
                "title_cn": "两数之和",
                "leetcode_slug": "two-sum",
                "page_number": None,
                "difficulty": "EASY",
                "status": "未做",
                "notes": None,
                "solution_url": None,
                "time_complexity": None,
                "space_complexity": None,
            }
        })()

        problem = create_problem(db, data)
        assert problem.id is not None
        assert problem.leetcode_number == "1"
        assert problem.leetcode_number_sort == 1

    def test_search_by_number(self, db):
        # 创建测试数据
        for i in ["1", "2", "3", "100", "200"]:
            p = Problem(
                leetcode_number=i,
                leetcode_number_sort=compute_sort_key(i),
                title=f"Problem {i}",
                difficulty="EASY",
                status="未做",
            )
            db.add(p)
        db.commit()

        problems, total = get_problems(db, q="1")
        assert total == 2  # "1" and "100"


# ========== 艾宾浩斯复习测试 ==========

class TestReviewSystem:
    def test_create_review_schedule(self, db):
        # 创建题目
        problem = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Two Sum",
            difficulty="EASY",
            status="已解",
        )
        db.add(problem)
        db.commit()

        schedule = create_review_schedule(db, problem.id)
        assert schedule.stage == 0
        assert schedule.is_completed == 0
        assert schedule.next_review_at > datetime.utcnow()

    def test_submit_review_good(self, db):
        # 创建题目和复习计划
        problem = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Two Sum",
            difficulty="EASY",
            status="已解",
        )
        db.add(problem)
        db.commit()

        schedule = create_review_schedule(db, problem.id)

        # 提交"基本记得"的复习
        record = submit_review(db, problem.id, 2)
        assert record.rating == 2

        # 验证阶段推进
        db.refresh(schedule)
        assert schedule.stage == 1
        assert schedule.is_completed == 0

    def test_submit_review_bad(self, db):
        # 创建题目
        problem = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Two Sum",
            difficulty="EASY",
            status="已解",
        )
        db.add(problem)
        db.commit()

        schedule = create_review_schedule(db, problem.id)

        # 提交"完全不会"的复习
        record = submit_review(db, problem.id, 0)
        assert record.rating == 0

        # 验证重置到第一阶段
        db.refresh(schedule)
        assert schedule.stage == 0
        db.refresh(problem)
        assert problem.status == "需复盘"

    def test_submit_review_fuzzy(self, db):
        # 创建题目
        problem = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Two Sum",
            difficulty="EASY",
            status="已解",
        )
        db.add(problem)
        db.commit()

        schedule = create_review_schedule(db, problem.id)
        original_stage = schedule.stage

        # 提交"比较模糊"的复习
        record = submit_review(db, problem.id, 1)
        assert record.rating == 1

        # 验证阶段不变
        db.refresh(schedule)
        assert schedule.stage == original_stage

    def test_review_completion(self, db):
        # 创建题目
        problem = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Two Sum",
            difficulty="EASY",
            status="已解",
        )
        db.add(problem)
        db.commit()

        schedule = create_review_schedule(db, problem.id)

        # 完成所有阶段
        for i in range(len(EBBINGHAUS_INTERVALS)):
            submit_review(db, problem.id, 3)
            db.refresh(schedule)

        assert schedule.is_completed == 1

    def test_get_next_review_priority(self, db):
        # 创建"需复盘"题目
        p1 = Problem(
            leetcode_number="1",
            leetcode_number_sort=1,
            title="Problem 1",
            difficulty="EASY",
            status="需复盘",
        )
        # 创建"已解"题目
        p2 = Problem(
            leetcode_number="2",
            leetcode_number_sort=2,
            title="Problem 2",
            difficulty="EASY",
            status="已解",
        )
        db.add_all([p1, p2])
        db.commit()

        # 应该优先返回"需复盘"的题目
        next_problem = get_next_review(db)
        assert next_problem.id == p1.id
