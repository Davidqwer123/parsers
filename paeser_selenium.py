from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import psycopg2
import json

url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_15_128GB_Black-p1044347.html"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

WebDriverWait(driver, 20).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
time.sleep(1)

try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
except:
    pass

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

driver.quit()


product = {}

product['full_name'] = soup.find("h1").text.strip() if soup.find("h1") else None
cl = soup.find("a", title=lambda t: t and "Колір" in t)
product["color"] = cl.text.strip() if cl else None
ml = soup.find("a", title=lambda t: t and "пам'ять" in t)
product["memory"] = ml.text.strip() if ml else None

vendor = None
for div in soup.find_all("div"):
    spans = div.find_all("span")
    if len(spans) >= 2 and spans[0].text.strip() == "Виробник":
        vendor = spans[1].text.strip()
        break
product["vendor"] = vendor

pb = soup.find("div", class_="price-wrapper")
product["price"] = pb.find("span").text.strip() if pb and pb.find("span") else None
st = soup.find("span", class_="product-price__current")
product["price_sale"] = st.text.strip() if st else None

imgs = []
for img in soup.find_all("img", class_="dots-image"):
    if img.get("src"):
        imgs.append(img.get("src"))
    if img.get("data-big-picture-src"):
        imgs.append(img.get("data-big-picture-src"))
product["images"] = imgs or None

sku = soup.find("span", class_="br-pr-code-val")
product["sku"] = sku.text.strip() if sku else None

rev = soup.find("a", href=lambda h: h and "reviews" in h)
if rev:
    num = "".join([c for c in rev.text if c.isdigit()])
    product["reviews_count"] = int(num) if num else 0
else:
    product["reviews_count"] = 0

dl = soup.find("a", title=lambda t: t and "Діагональ екрану" in t)
product["screen_diagonal"] = dl.text.strip() if dl else None

rl = soup.find("a", title=lambda t: t and "Роздільна здатність екрану" in t)
product["screen_resolution"] = rl.text.strip() if rl else None

product["specifications"] = {}
specs = soup.find("div", id="br-pr-7")
if specs:
    for item in specs.find_all("div", class_="br-pr-chr-item"):
        for row in item.find_all("div"):
            spans = row.find_all("span")
            if len(spans) >= 2:
                key = spans[0].text.strip()
                val = spans[1].text.strip()
                product["specifications"][key] = val

for k, v in product.items():
    print(f"{k}: {v}")
print("\nSpecifications:")
for k, v in product["specifications"].items():
    print(f"  • {k}: {v}")

try:
    with psycopg2.connect(
        dbname="parser_selenium",
        user="postgres",
        password="07031986",
        host="localhost",
        port="5432"
    ) as conn:
        with conn.cursor() as cur:
            images_json = json.dumps(product["images"], ensure_ascii=False)
            specs_json = json.dumps(product["specifications"], ensure_ascii=False)

            cur.execute(
                """
                INSERT INTO products (
                    full_name, color, memory, vendor,
                    price, price_sale, images, sku,
                    reviews_count, screen_diagonal,
                    screen_resolution, specifications
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    product["full_name"],
                    product["color"],
                    product["memory"],
                    product["vendor"],
                    product["price"],
                    product["price_sale"],
                    images_json,
                    product["sku"],
                    product["reviews_count"],
                    product["screen_diagonal"],
                    product["screen_resolution"],
                    specs_json
                )
            )
            conn.commit()
            print("\nДані успішно додано в PostgreSQL!")
except Exception as e:
    print("Помилка при записі в базу:", e)

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import time
# import psycopg2
# import json
#
# from test import conn
#
# url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_15_128GB_Black-p1044347.html"
#
# # ---------------- Selenium fix for Chrome 142 ----------------
# options = Options()
# options.add_argument("--headless=new")  # !!! critical fix
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("user-agent=Mozilla/5.0")
#
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#
# driver.get(url)
#
# # Чекаємо повне завершення завантаження DOM
# WebDriverWait(driver, 20).until(
#     lambda d: d.execute_script("return document.readyState") == "complete"
# )
#
# # Додаткова пауза (Chrome 142 інколи дорендерює елементи після readyState)
# time.sleep(1)
#
# # Чекаємо ключовий елемент
# try:
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.TAG_NAME, "h1"))
#     )
# except:
#     pass
#
# # Тільки тепер беремо HTML
# html = driver.page_source
# soup = BeautifulSoup(html, "html.parser")
#
# # ---------------- Парсинг ----------------
# product = {}
#
# # Назва
# product['full_name'] = (
#     soup.find("h1").text.strip() if soup.find("h1") else None
# )
#
# # Колір
# cl = soup.find("a", title=lambda t: t and "Колір" in t)
# product["color"] = cl.text.strip() if cl else None
#
# # Памʼять
# ml = soup.find("a", title=lambda t: t and "пам'ять" in t)
# product["memory"] = ml.text.strip() if ml else None
#
# # Виробник
# vendor = None
# for div in soup.find_all("div"):
#     spans = div.find_all("span")
#     if len(spans) >= 2 and spans[0].text.strip() == "Виробник":
#         vendor = spans[1].text.strip()
#         break
# product["vendor"] = vendor
#
# # Ціна
# pb = soup.find("div", class_="price-wrapper")
# product["price"] = (
#     pb.find("span").text.strip() if pb and pb.find("span") else None
# )
#
# # Акційна ціна
# st = soup.find("span", class_="product-price__current")
# product["price_sale"] = st.text.strip() if st else None
#
# # Зображення
# imgs = []
# for img in soup.find_all("img", class_="dots-image"):
#     if img.get("src"):
#         imgs.append(img.get("src"))
#     if img.get("data-big-picture-src"):
#         imgs.append(img.get("data-big-picture-src"))
# product["images"] = imgs or None
#
# # SKU
# sku = soup.find("span", class_="br-pr-code-val")
# product["sku"] = sku.text.strip() if sku else None
#
# # Відгуки
# rev = soup.find("a", href=lambda h: h and "reviews" in h)
# if rev:
#     num = "".join([c for c in rev.text if c.isdigit()])
#     product["reviews_count"] = int(num) if num else 0
# else:
#     product["reviews_count"] = 0
#
# # Діагональ
# dl = soup.find("a", title=lambda t: t and "Діагональ екрану" in t)
# product["screen_diagonal"] = dl.text.strip() if dl else None
#
# # Роздільна здатність
# rl = soup.find("a", title=lambda t: t and "Роздільна здатність екрану" in t)
# product["screen_resolution"] = rl.text.strip() if rl else None
#
# # Характеристики
# product["specifications"] = {}
# specs = soup.find("div", id="br-pr-7")
# if specs:
#     for item in specs.find_all("div", class_="br-pr-chr-item"):
#         for row in item.find_all("div"):
#             spans = row.find_all("span")
#             if len(spans) >= 2:
#                 key = spans[0].text.strip()
#                 val = spans[1].text.strip()
#                 product["specifications"][key] = val
#
# driver.quit()
#
# # ---------------- Вивід ----------------
# for k, v in product.items():
#     print(f"{k}: {v}")
#
# print("\nSpecifications:")
# for k, v in product["specifications"].items():
#     print(f"  • {k}: {v}")
#
#
# сonn = psycopg2.connect(
#     dbname="parser_selenium",     # назва твоєї БД
#     user="postgres",        # користувач PostgreSQL
#     password="07031986",       # ТВОЙ пароль PostgreSQL !!!
#     host="localhost",
#     port="5432"
# )
# cur = conn.cursor()
#
# # Конвертуємо список images у JSON-рядок
# images_json = json.dumps(product["images"], ensure_ascii=False)
#
# # Конвертуємо specifications у JSONB
# specs_json = json.dumps(product["specifications"], ensure_ascii=False)
#
# # ---------------- ЗАПИС У ТАБЛИЦЮ ----------------
# cur.execute(
#     """
#     INSERT INTO products (
#         full_name, color, memory, vendor,
#         price, price_sale, images, sku,
#         reviews_count, screen_diagonal,
#         screen_resolution, specifications
#     )
#     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """,
#     (
#         product["full_name"],
#         product["color"],
#         product["memory"],
#         product["vendor"],
#         product["price"],
#         product["price_sale"],
#         images_json,
#         product["sku"],
#         product["reviews_count"],
#         product["screen_diagonal"],
#         product["screen_resolution"],
#         specs_json
#     )
# )
#
# conn.commit()
# cur.close()
# conn.close()
#
# print("\nДані успішно додано в PostgreSQL!")