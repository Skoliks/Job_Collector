import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_main_page(url: str) -> str:
    with requests.Session() as session:
        try:
            logger.info(f"Request on {url}")
            response = session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout as e:
            logger.error("Timeout Error:", e)
        except requests.exceptions.RequestException as e:
            logger.error("Request Error:", e)

        return ""


def parse_main_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    blocks = soup.select("div.card-content")
    vacancies = []

    for block in blocks:
        title_tag = block.select_one("h2.title.is-5")
        company_tag = block.select_one("h3.subtitle.is-6.company")
        location_tag = block.select_one("p.location")
        date_tag = block.select_one("time")
        block_url = None

        block_tags = block.select("a")

        for tag_a in block_tags:
            if tag_a.text.strip() == "Apply":
                block_url = tag_a.get("href")
                break

        if (
            title_tag is None
            or company_tag is None
            or location_tag is None
            or date_tag is None
            or block_url is None
        ):
            continue

        vacancy_data = {
            "title": title_tag.text.strip(),
            "company": company_tag.text.strip(),
            "location": location_tag.text.strip(),
            "published_date": date_tag.text.strip(),
            "url": block_url.strip(),
            "salary": None
        }
        vacancies.append(vacancy_data)

    return vacancies


def get_details_from_vacancy_card(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    block = soup.select_one("div.content")
    description_tag = block.text.strip() if block else None
    return {"description": description_tag}


async def fetch_description_from_from_card(session: aiohttp.ClientSession, vacancy: dict, semaphore: asyncio.Semaphore) -> dict:
    url = vacancy["url"]

    logger.info(f"Request on {url}")

    try:
        async with semaphore:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
    except asyncio.TimeoutError as e:
        logger.error("Timeout Error:", e)
        vacancy["description"] = None
        return vacancy
    except aiohttp.ClientError as e:
        logger.error("Request Error:", e)
        vacancy["description"] = None
        return vacancy

    details_data = get_details_from_vacancy_card(html)
    vacancy["description"] = details_data["description"]
    return vacancy


async def enrich_vacancies_with_description(vacancies: list[dict]) -> list[dict]:
    semaphore = asyncio.Semaphore(5)

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_description_from_from_card(session, vacancy, semaphore)
            for vacancy in vacancies
        ]

        results = await asyncio.gather(*tasks)
        return results


def parse_fake_jobs() -> list[dict]:
    html = get_main_page(settings.fake_jobs_url)
    if not html:
        return []
    
    vacancies = parse_main_page(html)
    full_vacancies = asyncio.run(enrich_vacancies_with_description(vacancies))
    
    return full_vacancies
    