from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.routers.vacancies import router
from app.database import Base, engine


Base.metadata.create_all(bind=engine)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Job collector",
    version="alpha"
    )

app.include_router(router)


@app.get("/", include_in_schema=False)
def read_index():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/add", include_in_schema=False)
def read_add_page():
    return FileResponse(PROJECT_ROOT / "add.html")


@app.get("/style.css", include_in_schema=False)
def read_style():
    return FileResponse(PROJECT_ROOT / "style.css")


@app.get("/script.js", include_in_schema=False)
def read_script():
    return FileResponse(PROJECT_ROOT / "script.js")
