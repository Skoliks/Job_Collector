from pydantic import BaseModel
from datetime import datetime


class CreateVacancy(BaseModel):
    title: str
    company: str
    salary: int | None = None
    location: str | None = None
    published_date: str | None = None
    description: str | None = None
    url: str | None = None
    
    
class Vacancy(CreateVacancy):
    id: int
    created_at: datetime
    
    
class UpdateCompletelyVacancy(BaseModel):
    title: str
    company: str
    salary: int 
    location: str 
    published_date: str
    description: str 
    url: str 

class UpdateVacancy(BaseModel):
    title: str | None = None
    company: str | None = None
    salary: int | None = None
    location: str | None = None
    published_date: str | None = None
    description: str | None = None
    url: str | None = None
    
class ParsedVacancies(BaseModel):
    saved: list[Vacancy]
    created_count: int
    skipped_count: int