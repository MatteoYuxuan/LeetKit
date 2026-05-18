from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from models import Category
from routers import problems, categories, tags, stats, import_export, notes, reviews

DEFAULT_CATEGORIES = [
    "数组", "字符串", "链表", "栈", "队列", "哈希表",
    "二叉树", "图", "动态规划", "贪心", "二分查找",
    "回溯", "排序", "双指针", "滑动窗口", "位运算",
    "数学", "设计", "其他",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
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


app = FastAPI(title="LeetCode Notebook", lifespan=lifespan)

app.include_router(problems.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
