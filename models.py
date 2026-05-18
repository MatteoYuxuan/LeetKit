from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

problem_tags = Table(
    "problem_tags",
    Base.metadata,
    Column("problem_id", Integer, ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

problem_categories = Table(
    "problem_categories",
    Base.metadata,
    Column("problem_id", Integer, ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

note_categories = Table(
    "note_categories",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    problems: Mapped[list["Problem"]] = relationship("Problem", secondary=problem_categories, back_populates="categories")
    notes: Mapped[list["Note"]] = relationship("Note", secondary=note_categories, back_populates="categories")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    problems: Mapped[list["Problem"]] = relationship("Problem", secondary=problem_tags, back_populates="tags")
    notes: Mapped[list["Note"]] = relationship("Note", secondary=note_tags, back_populates="tags")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leetcode_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    leetcode_number_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_cn: Mapped[str | None] = mapped_column(String(200), nullable=True)
    leetcode_slug: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="未做")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    time_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    space_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    topic_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    ac_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    categories: Mapped[list["Category"]] = relationship("Category", secondary=problem_categories, back_populates="problems")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=problem_tags, back_populates="problems")
    reviews: Mapped[list["ReviewRecord"]] = relationship("ReviewRecord", back_populates="problem", cascade="all, delete-orphan")
    resources: Mapped[list["ProblemResource"]] = relationship("ProblemResource", back_populates="problem", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="markdown")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    categories: Mapped[list["Category"]] = relationship("Category", secondary=note_categories, back_populates="notes")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=note_tags, back_populates="notes")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    interval: Mapped[int] = mapped_column(Integer, nullable=False)
    time_spent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    problem: Mapped["Problem"] = relationship("Problem", back_populates="reviews")


class ProblemList(Base):
    __tablename__ = "problem_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    items: Mapped[list["ProblemListItem"]] = relationship("ProblemListItem", back_populates="problem_list", cascade="all, delete-orphan", order_by="ProblemListItem.sort_order")


class ProblemListItem(Base):
    __tablename__ = "problem_list_items"
    __table_args__ = (UniqueConstraint("problem_list_id", "problem_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_list_id: Mapped[int] = mapped_column(Integer, ForeignKey("problem_lists.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    problem_list: Mapped["ProblemList"] = relationship("ProblemList", back_populates="items")
    problem: Mapped["Problem"] = relationship("Problem")


class LeetCodeCookie(Base):
    __tablename__ = "leetcode_cookies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cookie_value: Mapped[str] = mapped_column(Text, nullable=False)
    leetcode_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ReviewSchedule(Base):
    __tablename__ = "review_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    stage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    problem: Mapped["Problem"] = relationship("Problem")


class ProblemResource(Base):
    __tablename__ = "problem_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)  # link, markdown, pdf, excel, image
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 外部链接
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 本地文件路径
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    problem: Mapped["Problem"] = relationship("Problem", back_populates="resources")
