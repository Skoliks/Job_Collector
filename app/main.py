from fastapi import FastAPI
from app.routers.vacancies import router
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job collector",
    version="alpha"
    )

app.include_router(router)
