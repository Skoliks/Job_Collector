from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.vacancy import Vacancy as VacancyModel
from app.parsers.asynco_parser import parse_fake_jobs
from app.parsers.hh_parser import parse_hh_vacancies
from app.schemas import CreateVacancy, UpdateCompletelyVacancy, UpdateVacancy

HH_DEFAULT_TEXT = ""
HH_DEFAULT_PERIOD = 7
HH_DEFAULT_PER_PAGE = 20


def get_all_vacancies(
    db: Session,
    q: str | None = None,
    title: str | None = None,
    salary: int | None = None,
    sort_by: str | None = None,
    company: str | None = None,
    location: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    query = db.query(VacancyModel)

    # Keyword search: each token must match at least one searchable field.
    if q:
        tokens = [token.strip() for token in q.split() if token.strip()]
        token_filters = []

        for token in tokens:
            one_token_filter = [
                VacancyModel.title.ilike(f"%{token}%"),
                VacancyModel.company.ilike(f"%{token}%"),
                VacancyModel.location.ilike(f"%{token}%"),
                VacancyModel.description.ilike(f"%{token}%"),
                VacancyModel.url.ilike(f"%{token}%"),
                VacancyModel.source.ilike(f"%{token}%"),
            ]

            if token.isdigit():
                one_token_filter.append(VacancyModel.salary == int(token))

            token_filters.append(or_(*one_token_filter))

        if token_filters:
            query = query.filter(and_(*token_filters))

    if title:
        query = query.filter(VacancyModel.title.ilike(f"%{title}%"))

    if salary:
        query = query.filter(VacancyModel.salary == salary)

    if company:
        query = query.filter(VacancyModel.company.ilike(f"%{company}%"))

    if location:
        query = query.filter(VacancyModel.location.ilike(f"%{location}%"))

    if sort_by == "salary":
        query = query.order_by(VacancyModel.salary)
    elif sort_by == "created_at":
        query = query.order_by(VacancyModel.created_at)
    else:
        query = query.order_by(VacancyModel.id.desc())

    query = query.offset(offset)
    query = query.limit(limit)

    return query.all()


def get_vacancies_by_id(id: int, db: Session):
    return db.query(VacancyModel).filter(VacancyModel.id == id).first()


def add_vacancy(vacancy_data: CreateVacancy, db: Session):
    new_vacancy = VacancyModel(**vacancy_data.model_dump())

    db.add(new_vacancy)
    db.commit()
    db.refresh(new_vacancy)

    return new_vacancy


def delete_vacancy_by_id(id: int, db: Session):
    vacancy = db.query(VacancyModel).filter(VacancyModel.id == id).first()

    if vacancy is None:
        return None

    db.delete(vacancy)
    db.commit()

    return vacancy


def update_completely_vacancy(id: int, new_data: UpdateCompletelyVacancy, db: Session):
    vacancy = db.query(VacancyModel).filter(VacancyModel.id == id).first()

    if vacancy is None:
        return None

    vacancy.title = new_data.title
    vacancy.company = new_data.company
    vacancy.salary = new_data.salary
    vacancy.location = new_data.location
    vacancy.published_date = new_data.published_date
    vacancy.description = new_data.description
    vacancy.url = new_data.url

    db.commit()
    db.refresh(vacancy)

    return vacancy


def update_vacancy_data(id: int, new_data: UpdateVacancy, db: Session):
    vacancy = db.query(VacancyModel).filter(VacancyModel.id == id).first()

    if vacancy is None:
        return None

    new_vacancy_data = new_data.model_dump(exclude_unset=True)

    for field, value in new_vacancy_data.items():
        setattr(vacancy, field, value)

    db.commit()
    db.refresh(vacancy)

    return vacancy


def find_vacancy_by_url(url: str, db: Session):
    return db.query(VacancyModel).filter(VacancyModel.url == url).first()


def if_vacancy_is_not_exist(vacancy_schema: CreateVacancy, db: Session):
    if vacancy_schema.url is not None:
        exists_vacancy = find_vacancy_by_url(vacancy_schema.url, db)
        if exists_vacancy is not None:
            return exists_vacancy, False

    new_vacancy = VacancyModel(**vacancy_schema.model_dump())

    db.add(new_vacancy)
    db.commit()
    db.refresh(new_vacancy)

    return new_vacancy, True


def update_vacancy_from_schema(vacancy: VacancyModel, vacancy_schema: CreateVacancy, db: Session):
    vacancy_data = vacancy_schema.model_dump()

    for field, value in vacancy_data.items():
        setattr(vacancy, field, value)

    db.commit()
    db.refresh(vacancy)

    return vacancy


def save_vacancies_from_parser(
    parsed_data: list[dict],
    db: Session,
    source: str,
    update_existing: bool = False
):
    if not parsed_data:
        return {
            "saved": [],
            "received_count": 0,
            "created_count": 0,
            "updated_count": 0,
            "skipped_count": 0
        }

    saved_vacancies = []
    created_count = 0
    updated_count = 0
    skipped_count = 0

    for vacancy in parsed_data:
        vacancy_schema = CreateVacancy(**vacancy, source=source)
        existing_vacancy = None

        if vacancy_schema.url is not None:
            existing_vacancy = find_vacancy_by_url(vacancy_schema.url, db)

        if existing_vacancy is None:
            created_vacancy, _ = if_vacancy_is_not_exist(vacancy_schema, db)
            saved_vacancies.append(created_vacancy)
            created_count += 1
            continue

        if update_existing:
            updated_vacancy = update_vacancy_from_schema(existing_vacancy, vacancy_schema, db)
            saved_vacancies.append(updated_vacancy)
            updated_count += 1
        else:
            saved_vacancies.append(existing_vacancy)
            skipped_count += 1

    return {
        "saved": saved_vacancies,
        "received_count": len(parsed_data),
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count
    }


def parse_hh_published_date(published_date: str | None) -> datetime | None:
    if not published_date:
        return None

    try:
        return datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def delete_outdated_hh_vacancies(db: Session, period: int):
    threshold = datetime.now(timezone.utc) - timedelta(days=period)
    deleted_count = 0

    hh_vacancies = db.query(VacancyModel).filter(VacancyModel.source == "hh").all()

    for vacancy in hh_vacancies:
        published_at = parse_hh_published_date(vacancy.published_date)

        if published_at is None:
            continue

        if published_at.astimezone(timezone.utc) < threshold:
            db.delete(vacancy)
            deleted_count += 1

    if deleted_count > 0:
        db.commit()

    return deleted_count


def save_parsed_vacancies(db: Session):
    parsed_data = parse_fake_jobs()
    result = save_vacancies_from_parser(
        parsed_data=parsed_data,
        db=db,
        source="fake_jobs"
    )

    return {
        "saved": result["saved"],
        "created_count": result["created_count"],
        "skipped_count": result["skipped_count"]
    }


def save_hh_parsed_vacancies(
    db: Session
):
    parsed_data = parse_hh_vacancies(
        text=HH_DEFAULT_TEXT,
        period=HH_DEFAULT_PERIOD,
        per_page=HH_DEFAULT_PER_PAGE
    )

    result = save_vacancies_from_parser(
        parsed_data=parsed_data,
        db=db,
        source="hh",
        update_existing=True
    )
    deleted_count = delete_outdated_hh_vacancies(db, HH_DEFAULT_PERIOD)

    return {
        "saved": result["saved"],
        "received_count": result["received_count"],
        "created_count": result["created_count"],
        "updated_count": result["updated_count"],
        "skipped_count": result["skipped_count"],
        "deleted_count": deleted_count
    }
