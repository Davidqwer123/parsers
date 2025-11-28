# import os
# import django
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
# django.setup()

import requests
from bs4 import BeautifulSoup
# from load_django import *
# from parsers_app import Tool
import psycopg2
import json
url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'TE': 'Trailers',
}

product = {}


r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")


try:
    product['full_name'] = soup.find('h1').text.strip()
except AttributeError:
    product['full_name'] = None

try:
    color_link = soup.find('a', title=lambda t: t and 'Колір' in t)
    if color_link:
        product['color'] = color_link.text.strip()
    else:
        product['color'] = None
except Exception:
    product['color'] = None


try:
    memory_link = soup.find('a', title=lambda t: t and "пам'ять" in t)
    if memory_link:
        product['memory'] = memory_link.text.strip()
    else:
        product['memory'] = None
except Exception:
    product['memory'] = None

try:
    vendor_div = soup.find('div', string=lambda x: False)
    vendor_div = None
    for div in soup.find_all('div'):
        spans = div.find_all('span')
        if len(spans) >= 2 and spans[0].text.strip() == "Виробник":
            vendor_div = div
            break
    if vendor_div:
        product['vendor'] = vendor_div.find_all('span')[1].text.strip()
    else:
        product['vendor'] = None
except Exception:
    product['vendor'] = None


try:
    price_tag = soup.find('div', class_='price-wrapper')
    if price_tag:
        # беремо текст з першого <span> всередині блока
        price_span = price_tag.find('span')
        product['price'] = price_span.text.strip() if price_span else None
    else:
        product['price'] = None
except Exception:
    product['price'] = None

try:
    product['price_sale'] = soup.find('span', class_='product-price__current').text.strip()
except:
    product['price_sale'] = None

try:
    images_tags = soup.find_all('img', class_='dots-image')  # всі <img> з цим класом
    images = []
    for img in images_tags:
        src = img.get('src')
        if src:
            images.append(src)
        big_src = img.get('data-big-picture-src')
        if big_src and big_src not in images:
            images.append(big_src)
    product['images'] = images if images else None
except Exception:
    product['images'] = None


try:
    sku_tag = soup.find('span', class_='br-pr-code-val')
    product['sku'] = sku_tag.text.strip() if sku_tag else None
except:
    product['sku'] = None


try:
    reviews_tag = soup.find('a', href=lambda href: href and 'reviews' in href)
    text = reviews_tag.text.strip() if reviews_tag else '0'
    product['reviews_count'] = int(''.join([c for c in text if c.isdigit()])) if text else 0
except:
    product['reviews_count'] = 0



try:
    diag_link = soup.find('a', title=lambda t: t and 'Діагональ екрану' in t)
    if diag_link:
        product['screen_diagonal'] = diag_link.text.strip()
    else:
        product['screen_diagonal'] = None
except Exception:
    product['screen_diagonal'] = None


try:
    resolution_link = soup.find('a', title=lambda t: t and 'Роздільна здатність екрану' in t)
    if resolution_link:
        product['screen_resolution'] = resolution_link.text.strip()  # наприклад "1320 х 2868"
    else:
        product['screen_resolution'] = None
except Exception:
    product['screen_resolution'] = None


product['specifications'] = {}

try:
    # шукаємо контейнер з усіма характеристиками
    specs_container = soup.find('div', id='br-pr-7')
    if specs_container:
        chr_items = specs_container.find_all('div', class_='br-pr-chr-item')
        for item in chr_items:
            spans_blocks = item.find_all('div')
            for block in spans_blocks:
                spans = block.find_all('span')
                if len(spans) >= 2:
                    key = spans[0].text.strip()
                    value = spans[1].text.strip()
                    product['specifications'][key] = value
except Exception:
    product['specifications'] = {}


for key, value in product.items():
    print(f"{key}: {value}")


for key, value in product['specifications'].items():
    print(f"  • {key}: {value}")


try:
    with psycopg2.connect(
        dbname="parser_requests",
        user="postgres",
        password="07031986",
        host="localhost",
        port="5432"
    ) as conn:
        with conn.cursor() as cur:
            images_json = json.dumps(product['images'], ensure_ascii=False)
            specs_json = json.dumps(product['specifications'], ensure_ascii=False)

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
                    product.get('full_name'),
                    product.get('color'),
                    product.get('memory'),
                    product.get('vendor'),
                    product.get('price'),
                    product.get('price_sale'),
                    images_json,
                    product.get('sku'),
                    product.get('reviews_count'),
                    product.get('screen_diagonal'),
                    product.get('screen_resolution'),
                    specs_json
                )
            )
            conn.commit()
            print("\nДані успішно додано в PostgreSQL!")
except Exception as e:
    print("Помилка при записі в базу:", e)