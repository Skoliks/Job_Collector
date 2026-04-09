from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CreateVacancy(BaseModel):
    title: str
    company: str
    salary: int | None = None
    location: str | None = None
    published_date: str | None = None
    description: str | None = None
    url: str | None = None
    source: str = "manual"
    
    
class Vacancy(CreateVacancy):
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

    saved: list[Vacancy]
    created_count: int
    skipped_count: int


class ParsedHhVacancies(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved: list[Vacancy]
    received_count: int
    created_count: int
    updated_count: int
    skipped_count: int
    deleted_count: int
