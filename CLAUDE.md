# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeetKit is a local LeetCode problem-solving notebook with an Ebbinghaus spaced-repetition review system. Python backend (FastAPI + SQLAlchemy + SQLite), monolithic vanilla JS frontend in a single HTML file. Runs entirely locally — no Docker, no CI/CD, no build step for the frontend.

## Common Commands

```bash
# Run the app (starts uvicorn with --reload on port 8000)
python main.py

# Run tests (uses in-memory SQLite, no real DB needed)
pytest

# Run a single test file
pytest tests/test_crud.py

# Run a single test function
pytest tests/test_crud.py::test_function_name

# Install dependencies
pip install -r requirements.txt
```

On Windows, `start.bat` launches on port 8001 with `--reload` and opens the browser.

## Architecture

### Backend Layers

- **`main.py`** — App entry point. Lifespan handler runs schema migrations on startup (`migrate_database()` using raw `ALTER TABLE ADD COLUMN` — no Alembic), creates tables, seeds 19 default categories. Mounts all routers under `/api`.
- **`models.py`** — 10 SQLAlchemy 2.0 models using `Mapped`/`mapped_column` style. 4 junction tables for many-to-many relationships (problem_tags, note_tags, problem_categories, note_categories).
- **`schemas.py`** — Pydantic v2 request/response schemas.
- **`crud.py`** — All DB operations in one file (~845 lines). Includes Ebbinghaus scheduling logic (intervals: 1, 2, 4, 7, 15, 30 days), review rating (0=forgot, 1=fuzzy, 2=good), LeetCode topic-to-category mapping, and sort key computation for special problem prefixes (LCP, LCR, LCS, LCOF, LCOF2).
- **`database.py`** — SQLAlchemy engine/session setup. Foreign keys enforced via `PRAGMA foreign_keys=ON`.
- **`security.py`** — Fernet encryption for LeetCode cookies. Auto-generates key in `.env`.

### Routers (`routers/`)

13 FastAPI routers, all mounted at `/api`. Key ones:
- `reviews.py` — Ebbinghaus review engine (next review, submit, stats, timeline)
- `leetcode.py` — Cookie-based LeetCode CN login, bulk import, sync progress/titles/categories
- `problems.py` — CRUD with pagination, filtering by difficulty/status/category/tag
- `problem_lists.py` — Custom collections with shareable base64-encoded URLs
- `stats.py` — Overview, category/difficulty breakdowns, progress over time, heatmap

### LeetCode Crawler (`crawler/`)

Async httpx client targeting `leetcode.cn`. Uses both REST (bulk problem list) and GraphQL (problem details, user progress). Module-level caching with 1-hour TTL. All queries in `queries.py`.

### Frontend (`static/index.html`)

~3000-line monolithic vanilla JS SPA. No framework, no build step. Tab-based navigation (Dashboard, Problems, Notes, Reviews, LeetCode, Problem Lists, Settings). Uses Chart.js and marked.js via CDN. All API calls through a single `api()` helper.

### Database

SQLite at `data/notebook.db`. Schema managed by `main.py`'s `migrate_database()` — reads existing columns via `PRAGMA table_info`, then runs `ALTER TABLE ADD COLUMN` for new ones. When adding a new column to a model, add it to the migration dict in `main.py` as well.

## Key Patterns

- All API routes return JSON, all prefixed with `/api`
- The frontend is Chinese-language; category names and UI text are in Chinese
- No authentication — this is a single-user local app
- Tests use in-memory SQLite (`:memory:`) and don't touch the real database
