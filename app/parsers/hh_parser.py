import requests


URL = "https://api.hh.ru/vacancies"

page = 0
per_page = 20
search_queries = 'Аналитик'
period = 7

headers = {"HH-User-Agent": "hh-learning-script (egor.aleksandravith@mail.ru)"}


def get_vacancies_page(url: str, params: dict, headers: dict) -> dict | None:
    
    try:
        response = requests.get(url=url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        print("Timeout Error:", e)
        return None
    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
        return None
    
    return response.json()


def parse_vacancy(vacancy: dict) -> dict:
    
    title = vacancy.get("name")
    
    employer = vacancy.get("employer")
    if employer is not None:
        company = employer.get("name")
    else:
        company = None
      
    salary_field = vacancy.get("salary")    
    if salary_field is not None:  
        salary = salary_field.get("from")
    else:
        salary = None
        
    address = vacancy.get("address")    
    if address is not None:
        city = address.get("city")
        street = address.get("street")
        building = address.get("building")
        
        location = f'''г. {"не указан" if city is None else city},ул. {"не указана" if street is None else street},д. {"не указан" if building is None else building}'''
        
    else:
        location = None
    
    published_date = vacancy.get("published_at")
    
    snippet = vacancy.get("snippet")
    if snippet is not None:
        requirement = snippet.get("requirement")
        responsibility = snippet.get("responsibility")
        description = f'''Что требуется для работы: {"не указано" if requirement is None else requirement} Что нужно делать: {"не указано" if responsibility is None else responsibility}'''
    else: 
        description = "Не указано"
        
    url = vacancy.get("alternate_url")
    
    return {
        "title": title,
        "company": company,
        "location": location,
        "published_date": published_date,
        "url": url,
        "salary": salary,
        "description": description
    }
    

def collect_vacancies(url: str, headers: dict, text: str, period: int, max_pages: int, per_page: int) -> list[dict]:
    vacancies = []
    
    first_params = {
        'text': text,
        'period': period,
        'per_page': per_page,
        'page': 0,
        }
    
    json_data_for_pages = get_vacancies_page(url=url, params=first_params, headers=headers)
    
    if json_data_for_pages is None:
        return []
    
    total_pages = json_data_for_pages.get('pages',0)
    pages_for_parse = min(max_pages, total_pages)
    
    for page in range(pages_for_parse):
        params = {
            'text': text,
            'period': period,
            'per_page': per_page,
            'page': page,
        }
        
        json_data = get_vacancies_page(url=url, params=params, headers=headers)
        
        if json_data is None:
            continue
        
        items = json_data.get('items', [])
        
        for vacancy in items:
            parsed_vacancy = parse_vacancy(vacancy)
            vacancies.append(parsed_vacancy)
        
    return vacancies


print(collect_vacancies(url=URL,headers=headers, text="Аналитик", period=7, max_pages=10, per_page=20))       
    
    