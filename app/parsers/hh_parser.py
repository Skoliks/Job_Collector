import aiohttp
import asyncio
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

headers = {"HH-User-Agent": f"hh-learning-script ({settings.hh_api_email})"}


async def get_vacancies_page(
    url: str, 
    params: dict, 
    headers: dict, 
    session: aiohttp.ClientSession, 
    semaphore: asyncio.Semaphore
) -> dict | None:
    try:
        async with semaphore:
            logger.info(f"Request on: {url}")
            async with session.get(url=url, params=params, headers=headers, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
    except asyncio.TimeoutError as e:
        logger.error("Timeout Error:", e)
        return None
    except aiohttp.ClientError as e:
        logger.error("Request Error:", e)
        return None
    
    logger.info("Request completed successfully!")
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
    

async def collect_vacancies(url: str, headers: dict, text: str, period: int, per_page: int) -> list[dict]:
    vacancies = []
    semaphore = asyncio.Semaphore(5)
    
    async with aiohttp.ClientSession() as session:
        first_params = {
            'text': text,
            'period': period,
            'per_page': per_page,
            'page': 0,
            }
        
        logger.info("Request for getting max. page count")
        json_data_for_pages = await get_vacancies_page(url=url, params=first_params, headers=headers, semaphore=semaphore, session=session)
        
        if json_data_for_pages is None:
            logger.error("Request completed with errror. Count of max page not found!")
            return []
        
        pages_for_parse = json_data_for_pages.get('pages', 0)
        results = [json_data_for_pages]
        tasks = []
        
        for page in range(1, pages_for_parse):
            params = {
                'text': text,
                'period': period,
                'per_page': per_page,
                'page': page,
            }
            
            logger.info(f"Request on {page}")
            task = get_vacancies_page(url=url, params=params, headers=headers, semaphore=semaphore, session=session)
            
            tasks.append(task)
            
        if tasks:
            results.extend(await asyncio.gather(*tasks))
            
        for page, json_data in enumerate(results):   
            if json_data is None:
                logger.error(f"Page {page} skipped due to error")
                continue
                
            items = json_data.get('items', [])
        
            if not items:
                logger.info(f"Vacancies on the page {page} not found!")
            else:
                logger.info(f"received {len(items)} vacancies on page {page}")
                
            for vacancy in items:
                parsed_vacancy = parse_vacancy(vacancy)
                vacancies.append(parsed_vacancy)
                
    logger.info(f"Count of vacancies:{len(vacancies)}")
    return vacancies
     
    
def parse_hh_vacancies(text: str, period: int, per_page: int) -> list[dict]:
    return asyncio.run(
        collect_vacancies(
            url=settings.hh_api_url,
            headers=headers,
            text=text,
            period=period,
            per_page=per_page
        )
    )
 

