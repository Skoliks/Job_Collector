from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import Vacancy, CreateVacancy, UpdateCompletelyVacancy, UpdateVacancy, ParsedVacancies
from app.services.vacancy_service import (
    get_all_vacancies,
    get_vacancies_by_id,
    add_vacancy,
    delete_vacancy_by_id,
    update_completely_vacancy,
    update_vacancy_data)
from app.services.vacancy_service import save_parsed_vacancies


router = APIRouter(prefix="/vacancies", tags=["Vacancies"])

@router.get("/", response_model=list[Vacancy])
def get_all_vacancies_route(
    q: str | None = None,
    title: str | None = None,
    salary: int | None = None,
    company: str | None = None,
    location: str | None = None,
    sort_by: str | None = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    if sort_by not in (None, "salary", "created_at"):
        raise HTTPException(status_code=400, detail="Invalid sort field")
    
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be >= 1")
    
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be >= 0")
    
    return get_all_vacancies(
        db=db,
        q=q,
        title=title,
        salary=salary,
        company=company,
        location=location,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )


@router.get("/{id}", response_model=Vacancy)
def get_vacancy_by_id_route(id: int, db: Session = Depends(get_db)):
    vacancy = get_vacancies_by_id(id, db)
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return vacancy


@router.post("/", response_model=Vacancy)
def create_vacancy_route(data: CreateVacancy, db: Session = Depends(get_db)):
    return add_vacancy(data, db)


@router.delete("/{id}", response_model=Vacancy)
def delete_vacancy_route(id: int, db: Session = Depends(get_db)):
    vacancy = delete_vacancy_by_id(id, db)
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return vacancy


@router.put("/{id}", response_model=Vacancy)
def change_completely_vacancy_route(id: int, new_data: UpdateCompletelyVacancy, db: Session = Depends(get_db)):
    vacancy = update_completely_vacancy(id, new_data, db)
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return vacancy


@router.patch("/{id}", response_model=Vacancy)
def change_vacancy_data(id: int, new_data: UpdateVacancy, db: Session = Depends(get_db)):
    vacancy = update_vacancy_data(id, new_data, db)
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return vacancy
 
 
@router.post("/parse-fake", response_model=ParsedVacancies)
def parsed_vacancies_route(db: Session = Depends(get_db)):
    vacancies = save_parsed_vacancies(db)
    
    if not vacancies["saved"]:
        raise HTTPException(status_code=422, detail="No vacancies found")
    
    return vacancies
