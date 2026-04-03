import requests
from bs4 import BeautifulSoup
import time
#это просто файл для тестов

html = """
<html>
  <body>
    <div class="vacancy">
      <h2 class="title">Python Developer</h2>
      <div class="company">Google</div>
      <div class="salary">100000</div>
    </div>

    <div class="vacancy">
      <h2 class="title">Backend Engineer</h2>
      <div class="company">Amazon</div>
      <div class="salary">150000</div>
    </div>

    <div class="vacancy">
      <h2 class="title">FastAPI Developer</h2>
      <div class="company">OpenAI</div>
      <div class="salary">200000</div>
    </div>
  </body>
</html>
"""

#print(vacancies_from_html(html=html))

URL = "https://realpython.github.io/fake-jobs/"

try:
  response = requests.get(URL, timeout=10)
  response.raise_for_status()
except requests.exceptions.Timeout:
    print("Слишком долго грузит! Код 422")
except requests.exceptions.RequestException:
    print("Ну эт чет с подключением плохо")
    
html = response.text


def get_details_from_block(html: str) -> dict:
  soup = BeautifulSoup(html, "html.parser")
  block = soup.select_one("div.content")
  description_tag = block.text.strip() if block else None
  return {"description": description_tag}


#это парсер для сайта, который специально предназначен для обучения парсингу
# тут код полностью синхронный и выполняется довольно долго 
#title, company, date, location
def vavancies_from_html_test_func(html: str) -> list[dict]:
  soup = BeautifulSoup(html, "html.parser")
  
  blocks = soup.select("div.card-content")
  vacancies = []
  
  with requests.Session() as session:
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
             
        print("загрузка данных:", block_url)
        
        try:
          response = session.get(block_url.strip(), timeout=10)
          response.raise_for_status()
        except requests.exceptions.Timeout:
          print(f"слишком долго грузит файл {block_url}")
          continue
        except requests.exceptions.RequestException:
          print(f"Ошибка при загрузке {block_url}")
          continue
        
        time.sleep(0.2)
        
        html_block = response.text 
        details_data = get_details_from_block(html_block)
        
        vacancy_data = {
          "title": title_tag.text.strip(),
          "company": company_tag.text.strip(),
          "location": location_tag.text.strip(),
          "date": date_tag.text.strip(),
          "description": details_data["description"],
          "URL": block_url.strip()
        }
        vacancies.append(vacancy_data)
    
    return vacancies


print(vavancies_from_html_test_func(html))