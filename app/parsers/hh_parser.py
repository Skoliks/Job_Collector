import aiohttp
import asyncio

URL = "https://api.hh.ru/vacancies"

headers = {"HH-User-Agent": "hh-learning-script (egor.aleksandravith@mail.ru)"}


async def get_vacancies_page(
    url: str, 
    params: dict, 
    headers: dict, 
    session: aiohttp.ClientSession, 
    semaphore: asyncio.Semaphore
) -> dict | None:
    try:
        async with semaphore:
            print(f"Идет запрос на {url}")
            async with session.get(url=url, params=params, headers=headers, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
    except asyncio.TimeoutError as e:
        print("Timeout Error:", e)
        return None
    except aiohttp.ClientError as e:
        print("Request Error:", e)
        return None
    
    print("Загрузка совершена успешно!")
    return data


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
    

async def collect_vacancies(url: str, headers: dict, text: str, period: int, max_pages: int, per_page: int) -> list[dict]:
    vacancies = []
    semaphore = asyncio.Semaphore(5)
    
    async with aiohttp.ClientSession() as session:
        first_params = {
            'text': text,
            'period': period,
            'per_page': per_page,
            'page': 0,
            }
        
        print("Идет запрос на страницу для получения макс. страниц")
        json_data_for_pages = await get_vacancies_page(url=url, params=first_params, headers=headers, semaphore=semaphore, session=session)
        
        if json_data_for_pages is None:
            print("Запрос завершился ошибкой. Макс. страниц не найдено")
            return []
        
        total_pages = json_data_for_pages.get('pages',0)
        pages_for_parse = min(max_pages, total_pages)
        tasks = []
        
        for page in range(pages_for_parse):
            params = {
                'text': text,
                'period': period,
                'per_page': per_page,
                'page': page,
            }
            
            print(f"Идет запрос на страницу {page}")
            task = get_vacancies_page(url=url, params=params, headers=headers, semaphore=semaphore, session=session)
        
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
            
        for page, json_data in enumerate(results):   
            if json_data is None:
                print(f"Страница {page} пропущена из-за ошибки")
                continue
                
            items = json_data.get('items', [])
        
            if not items:
                print(f"Вакансий на странице {page} не найдено!")
            else:
                print(f"Получено {len(items)} вакансий на странице {page}")
                
            for vacancy in items:
                parsed_vacancy = parse_vacancy(vacancy)
                vacancies.append(parsed_vacancy)
                
    print(f"Кол-во обработанных вакансий:{len(vacancies)}")
    return vacancies
     
    
def parse_hh_vacancies(text: str, period: int, max_pages: int, per_page: int) -> list[dict]:
    return asyncio.run(
        collect_vacancies(
            url=URL,
            headers=headers,
            text=text,
            period=period,
            max_pages=max_pages,
            per_page=per_page
        )
    )
