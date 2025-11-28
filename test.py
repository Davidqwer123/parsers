from playwright.sync_api import sync_playwright
import psycopg2
import json
import time

# -------------------------------
# 1. Функція безпечного витягування
# -------------------------------
def safe_text(page, selector, attr=None):
    try:
        el = page.query_selector(selector)
        if el:
            return el.get_attribute(attr).strip() if attr else el.inner_text().strip()
        return None
    except:
        return None

# -------------------------------
# 2. ПІДКЛЮЧЕННЯ ДО БАЗИ ДАНИХ
# -------------------------------
conn = psycopg2.connect(
    dbname="parser_playwright",
    user="postgres",
    password="07031986",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# -------------------------------
# 3. ПАРСЕР
# -------------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
    context = browser.new_context()
    page = context.new_page()

    page.goto(
        "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html",
        timeout=60000,
        wait_until="domcontentloaded"
    )

    time.sleep(5)

    product = {}

    # Основні дані
    product['full_name'] = safe_text(page, "h1")
    product["color"] = safe_text(page, "a[title*='Колір']")
    product["memory"] = safe_text(page, "a[title*='пам']")

    # Виробник
    vendor = None
    divs = page.query_selector_all("div")
    for div in divs:
        spans = div.query_selector_all("span")
        if len(spans) >= 2:
            key = spans[0].inner_text().strip()
            if key == "Виробник":
                vendor = spans[1].inner_text().strip()
                break
    product["vendor"] = vendor

    # Ціна
    product["price"] = safe_text(page, ".price-wrapper span")
    product["price_sale"] = safe_text(page, ".product-price__current")

    # Зображення
    imgs = []
    for img in page.query_selector_all("img.dots-image"):
        src = img.get_attribute("src")
        if src:
            imgs.append(src)
        big_src = img.get_attribute("data-big-picture-src")
        if big_src:
            imgs.append(big_src)
    product["images"] = imgs or None

    # SKU
    product["sku"] = safe_text(page, ".br-pr-code-val")

    # Відгуки
    rev = page.query_selector("a[href*='reviews']")
    if rev:
        num = "".join([c for c in rev.inner_text() if c.isdigit()])
        product["reviews_count"] = int(num) if num else 0
    else:
        product["reviews_count"] = 0

    # Діагональ та роздільна здатність
    product["screen_diagonal"] = safe_text(page, "a[title*='Діагональ екрану']")
    product["screen_resolution"] = safe_text(page, "a[title*='Роздільна здатність екрану']")

    # Характеристики
    product["specifications"] = {}
    specs_div = page.query_selector("#br-pr-7")
    if specs_div:
        items = specs_div.query_selector_all(".br-pr-chr-item")
        for item in items:
            rows = item.query_selector_all("div")
            for row in rows:
                spans = row.query_selector_all("span")
                if len(spans) >= 2:
                    key = spans[0].inner_text().strip()
                    val = spans[1].inner_text().strip()
                    product["specifications"][key] = val

    # -------------------------------
    # 4. ЗБЕРЕЖЕННЯ В POSTGRES
    # -------------------------------
    cur.execute("""
        INSERT INTO products (
            full_name, color, memory, vendor, price, price_sale,
            images, sku, reviews_count, screen_diagonal,
            screen_resolution, specifications
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        product["full_name"],
        product["color"],
        product["memory"],
        product["vendor"],
        product["price"],
        product["price_sale"],
        json.dumps(product["images"]),
        product["sku"],
        product["reviews_count"],
        product["screen_diagonal"],
        product["screen_resolution"],
        json.dumps(product["specifications"])
    ))

    conn.commit()
    browser.close()

# Закриваємо підключення
cur.close()
conn.close()

print("Дані успішно збережено в PostgreSQL!")

# from playwright.sync_api import sync_playwright
# import time
#
# def safe_text(page, selector, attr=None):
#     try:
#         el = page.query_selector(selector)
#         if el:
#             return el.get_attribute(attr).strip() if attr else el.inner_text().strip()
#         return None
#     except:
#         return None
#
# with sync_playwright() as p:
#     browser = p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
#     context = browser.new_context()
#     page = context.new_page()
#
#     page.goto(
#         "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html",
#         timeout=60000,
#         wait_until="domcontentloaded"
#     )
#
#     # Чекаємо, поки JS підвантажить дані
#     time.sleep(5)
#
#     product = {}
#
#     # Назва продукту
#     product['full_name'] = safe_text(page, "h1")
#
#     # Колір
#     product["color"] = safe_text(page, "a[title*='Колір']")
#
#     # Пам'ять
#     product["memory"] = safe_text(page, "a[title*='пам']")  # 'пам' для різних варіантів
#
#     # Виробник
#     vendor = None
#     divs = page.query_selector_all("div")
#     for div in divs:
#         spans = div.query_selector_all("span")
#         if len(spans) >= 2:
#             key = spans[0].inner_text().strip()
#             if key == "Виробник":
#                 vendor = spans[1].inner_text().strip()
#                 break
#     product["vendor"] = vendor
#
#     # Ціна
#     product["price"] = safe_text(page, ".price-wrapper span")
#
#     # Акційна ціна
#     product["price_sale"] = safe_text(page, ".product-price__current")
#
#     # Зображення
#     imgs = []
#     for img in page.query_selector_all("img.dots-image"):
#         src = img.get_attribute("src")
#         if src:
#             imgs.append(src)
#         big_src = img.get_attribute("data-big-picture-src")
#         if big_src:
#             imgs.append(big_src)
#     product["images"] = imgs or None
#
#     # SKU
#     product["sku"] = safe_text(page, ".br-pr-code-val")
#
#     # Відгуки
#     rev = page.query_selector("a[href*='reviews']")
#     if rev:
#         num = "".join([c for c in rev.inner_text() if c.isdigit()])
#         product["reviews_count"] = int(num) if num else 0
#     else:
#         product["reviews_count"] = 0
#
#     # Діагональ екрану
#     product["screen_diagonal"] = safe_text(page, "a[title*='Діагональ екрану']")
#
#     # Роздільна здатність
#     product["screen_resolution"] = safe_text(page, "a[title*='Роздільна здатність екрану']")
#
#     # Характеристики
#     product["specifications"] = {}
#     specs_div = page.query_selector("#br-pr-7")
#     if specs_div:
#         items = specs_div.query_selector_all(".br-pr-chr-item")
#         for item in items:
#             rows = item.query_selector_all("div")
#             for row in rows:
#                 spans = row.query_selector_all("span")
#                 if len(spans) >= 2:
#                     key = spans[0].inner_text().strip()
#                     val = spans[1].inner_text().strip()
#                     product["specifications"][key] = val
#
#     # Вивід результату
#     for k, v in product.items():
#         print(f"{k}: {v}")
#
#     browser.close()
#
