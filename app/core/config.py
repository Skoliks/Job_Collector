from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    hh_api_url: str = "https://api.hh.ru/vacancies"
    hh_api_email: str
    fake_jobs_url: str = "https://realpython.github.io/fake-jobs/"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    
settings = Settings()