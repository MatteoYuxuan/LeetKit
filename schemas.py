from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


# --- Category ---

class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=50)
    description: str | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryResponse(CategoryCreate):
    id: int
    problem_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# --- Tag ---

class TagCreate(BaseModel):
    name: str = Field(..., max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    color: str | None = None


class TagResponse(TagCreate):
    id: int
    problem_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# --- Problem ---

class ProblemCreate(BaseModel):
    leetcode_number: int
    title: str = Field(..., max_length=200)
    title_cn: str | None = None
    leetcode_slug: str | None = None
    page_number: int | None = None
    difficulty: Literal["EASY", "MEDIUM", "HARD"]
    status: Literal["未做", "在做", "已解", "需复盘"] = "未做"
    category_ids: list[int] = []
    notes: str | None = None
    solution_url: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    tag_ids: list[int] = []


class ProblemUpdate(BaseModel):
    title: str | None = None
    title_cn: str | None = None
    leetcode_slug: str | None = None
    page_number: int | None = None
    difficulty: Literal["EASY", "MEDIUM", "HARD"] | None = None
    status: Literal["未做", "在做", "已解", "需复盘"] | None = None
    category_ids: list[int] | None = None
    notes: str | None = None
    solution_url: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    tag_ids: list[int] | None = None


class ProblemResponse(BaseModel):
    id: int
    leetcode_number: int
    title: str
    title_cn: str | None
    leetcode_slug: str | None
    page_number: int | None
    difficulty: str
    status: str
    categories: list[CategoryResponse]
    tags: list[TagResponse]
    notes: str | None
    solution_url: str | None
    time_complexity: str | None
    space_complexity: str | None
    ac_rate: float | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProblemListResponse(BaseModel):
    items: list[ProblemResponse]
    total: int
    page: int
    page_size: int


# --- Note ---

class NoteCreate(BaseModel):
    title: str = Field(..., max_length=200)
    page_number: int | None = None
    category_ids: list[int] = []
    content: str | None = None
    tag_ids: list[int] = []


class NoteUpdate(BaseModel):
    title: str | None = None
    page_number: int | None = None
    category_ids: list[int] | None = None
    content: str | None = None
    tag_ids: list[int] | None = None


class NoteResponse(BaseModel):
    id: int
    title: str
    page_number: int | None
    categories: list[CategoryResponse]
    tags: list[TagResponse]
    content: str | None
    format: str = "markdown"
    file_path: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int


# --- Stats ---

class DifficultyStats(BaseModel):
    total: int
    已解: int


class StatsOverview(BaseModel):
    total: int
    note_total: int
    by_status: dict[str, int]
    by_difficulty: dict[str, DifficultyStats]


class CategoryStats(BaseModel):
    name: str
    count: int


class ProgressPoint(BaseModel):
    week: str
    cumulative_solved: int


# --- Import/Export ---

class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


# --- Review ---

class ReviewSubmit(BaseModel):
    problem_id: int
    rating: Literal[0, 1, 2, 3]


class ReviewResponse(BaseModel):
    id: int
    problem_id: int
    rating: int
    interval: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReviewNextResponse(BaseModel):
    problem: ProblemResponse
    review_count: int
    last_rating: int | None


class ReviewStatsResponse(BaseModel):
    pending: int
    completed_today: int
    total_reviews: int
