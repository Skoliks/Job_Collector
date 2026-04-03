from app.models.vacancy import Vacancy as VacancyModel
from sqlalchemy.orm import Session
from app.schemas import CreateVacancy, UpdateCompletelyVacancy, UpdateVacancy
from app.parsers.asynco_parser import parse_fake_jobs

def get_all_vacancies(
    db: Session,
    title: str | None = None,
    salary: int | None = None,
    sort_by: str | None = None,
    company: str | None = None,
    location: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    query = db.query(VacancyModel)
    
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
    db.commit
    
    return vacancy


def update_completely_vacancy(id: int, new_data: UpdateCompletelyVacancy, db: Session):
    vacancy = db.query(VacancyModel).filter(VacancyModel.id == id).first()
    
    if vacancy is None:
        return None

    vacancy.title = new_data.title
    vacancy.company = new_data.company
    vacancy.salary = new_data.salary
    
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
        
        

def save_parsed_vacancies(db: Session):
    
    parsed_data = parse_fake_jobs()
    
    if not parsed_data:
        return {
            "saved": [],
            "created_count": 0,
            "skipped_count": 0
        }
    
    saved_vacancies = []
    created_count = 0
    skipped_count = 0
    
    for vacancy in parsed_data:
        vacancy_schema = CreateVacancy(**vacancy)
        create_new_vacancy, created = if_vacancy_is_not_exist(vacancy_schema, db)
        saved_vacancies.append(create_new_vacancy)
        
        if created:
            created_count += 1
        else:
            skipped_count += 1
        
        
    return {
            "saved": saved_vacancies,
            "created_count": created_count,
            "skipped_count": skipped_count
        }
    
    
    