from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from models import Category
from routers import problems, categories, tags, stats, import_export, notes, reviews, search, problem_lists, leetcode, batch, resources, checkin

DEFAULT_CATEGORIES = [
    "数组", "字符串", "链表", "栈", "队列", "哈希表",
    "二叉树", "图", "动态规划", "贪心", "二分查找",
    "回溯", "排序", "双指针", "滑动窗口", "位运算",
    "数学", "设计", "其他",
]


def migrate_database():
    """自动迁移数据库，添加新字段和表"""
    import sqlite3
    import os

    db_path = os.path.join(os.path.dirname(__file__), "data", "notebook.db")
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取 problems 表现有列
    cursor.execute("PRAGMA table_info(problems)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # problems 表新增字段
    new_columns = {
        "leetcode_slug": "TEXT",
        "topic_tags": "TEXT",
        "ac_rate": "REAL",
        "last_synced_at": "TIMESTAMP",
        "solved_at": "TIMESTAMP",
    }
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE problems ADD COLUMN {col_name} {col_type}")

    # 获取 notes 表现有列
    cursor.execute("PRAGMA table_info(notes)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # notes 表新增字段
    new_columns = {
        "format": "TEXT DEFAULT 'markdown'",
        "file_path": "TEXT",
    }
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE notes ADD COLUMN {col_name} {col_type}")

    # 获取 review_records 表现有列
    cursor.execute("PRAGMA table_info(review_records)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "time_spent" not in existing_columns:
        cursor.execute("ALTER TABLE review_records ADD COLUMN time_spent INTEGER")

    # 创建 daily_checkins 表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date VARCHAR(10) UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 先执行迁移（对已有数据库添加新字段）
    migrate_database()
    # 再创建所有表（包括新增的表）
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            for name in DEFAULT_CATEGORIES:
                db.add(Category(name=name))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="LeetKit", lifespan=lifespan)

app.include_router(problems.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(problem_lists.router, prefix="/api")
app.include_router(leetcode.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(checkin.router, prefix="/api")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/shared")
def serve_shared():
    return FileResponse("static/shared.html")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
