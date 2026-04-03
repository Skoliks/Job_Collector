from sqlalchemy import Column, Float, String, Integer, DateTime, Text
from datetime import datetime
from app.database import Base


class Vacancy(Base):
    __tablename__ = "vacancies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    salary = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    published_date = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)