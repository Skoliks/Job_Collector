from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings


engine = create_engine(url=settings.database_url, connect_args=
                       {"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if not inspector.has_table("vacancies"):
        return

    columns = {column["name"] for column in inspector.get_columns("vacancies")}

    with engine.begin() as connection:
        if "source" not in columns:
            connection.execute(text("ALTER TABLE vacancies ADD COLUMN source VARCHAR"))

        connection.execute(
            text("UPDATE vacancies SET source = 'manual' WHERE source IS NULL")
        )

        indexes = {index["name"] for index in inspector.get_indexes("vacancies")}
        if "ix_vacancies_url_unique" not in indexes:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_vacancies_url_unique "
                    "ON vacancies (url) WHERE url IS NOT NULL"
                )
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
