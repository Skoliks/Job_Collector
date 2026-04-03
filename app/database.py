from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine


#URL = "postgresql+psycopg2://postgres:forgive12@localhost:5432/job_collector_db"
LITE_URL = "sqlite:///./job_collector.db"

engine = create_engine(url=LITE_URL, connect_args=
                       {"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    