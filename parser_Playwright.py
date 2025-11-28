#!/usr/bin/env python
# -*- coding: utf-8 -*-



import asyncio
import re
import json
import csv
from time import sleep
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

# Сторінка для парсингу (заміни на свій URL або передавай список URL-ів)
URLS = [
    "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"
]

OUTPUT_JSON = "output.json"
OUTPUT_CSV = "output.csv"


async def human_like_actions(page: Page):
    try:
        await page.mouse.move(300, 300)
        await page.mouse.move(600, 400, steps=10)
    except Exception:
        pass


    try:
        await page.evaluate("""() => {
            window.scrollBy(0, window.innerHeight / 2);
        }""")
        await asyncio.sleep(0.5)
        await page.evaluate("""() => {
            window.scrollBy(0, -100);
        }""")
        await asyncio.sleep(0.3)
    except Exception:
        pass


async def safe_get_text(locator, default: Optional[str] = None) -> Optional[str]:
    try:
        return (await locator.inner_text()).strip()
    except Exception:
        return default


async def extract_specs_from_table(page: Page) -> Dict[str, str]:
    specs = {}
    try:
        if await page.locator("text=Характеристики").count():
            try:
                await page.locator("text=Характеристики").click(timeout=5000)
            except Exception:
                pass
            await asyncio.sleep(0.5)

        if await page.locator("table").count():
            rows = await page.locator("table tr").all()
            for row in rows:
                try:
                    tds = row.locator("td")
                    if await tds.count() >= 2:
                        key = (await tds.nth(0).inner_text()).strip()
                        val = (await tds.nth(1).inner_text()).strip()
                        if key:
                            specs[key] = val
                except Exception:
                    continue
    except Exception:
        pass
    return specs


async def parse_product(page: Page, url: str) -> Dict:
    result = {
        "url": url,
        "title": None,
        "sku": None,
        "price": None,
        "old_price": None,
        "images": [],
        "specs": {},
        "availability": None,
        "rating": None,
        "reviews_count": None,
        "error": None,
    }

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except PlaywrightTimeoutError:
        pass

    await human_like_actions(page)

    title = None
    for attempt in range(3):
        try:
            if await page.locator("h1.pdp-header__title-text").count():
                title = await page.locator("h1.pdp-header__title-text").inner_text()
            elif await page.locator("h1").count():
                title = (await page.locator("h1").first.inner_text()).strip()
            if title:
                result["title"] = title.strip()
                break
        except PlaywrightTimeoutError:
            pass
        except Exception:
            pass
        await asyncio.sleep(1 + attempt)  # backoff

    if not result["title"]:
        result["error"] = "Title not found"
    try:
        if await page.locator("div:span('Штрихкод')").count():
            raw = await page.locator("div:span('Штрихкод')").inner_text()
            sku_match = re.search(r"Штрихкод", raw)
            if sku_match:
                result["sku"] = sku_match.group(1).strip()
            else:
                n = re.search(r"(\d{4,})", raw)
                if n:
                    result["span"] = n.group(1)
        elif await page.locator("br-pr-code-val").count():
            raw = await page.locator("br-pr-code-val").inner_text()
            result["span"] = raw.strip()
    except Exception:
        pass

    try:
        pb = page.locator("div.price-wrapper")

        if await pb.count() > 0:
            span = pb.locator("span")
            curr = pb.locator("strong")

            if await span.count() > 0:
                raw_num = (await span.inner_text()).strip()
            else:
                raw_num = None

            if await curr.count() > 0:
                raw_curr = (await curr.inner_text()).strip()
            else:
                raw_curr = ""

            if raw_num:
                price = raw_num.replace(" ", "")
            else:
                price = None

        else:
            price = None

    except Exception:
        price = None


    try:
        img_selectors = [".pdp-gallery img", ".gallery img", "img.product-image", "img"]
        seen = set()
        for sel in img_selectors:
            if await page.locator(sel).count():
                imgs = await page.locator(sel).all()
                for img in imgs:
                    src = await img.get_attribute("src") or await img.get_attribute("data-src") or await img.get_attribute("data-lazy")
                    if src:
                        src = src.strip()
                        if src.startswith("//"):
                            src = "https:" + src
                        if src.startswith("/"):
                            from urllib.parse import urljoin
                            src = urljoin(url, src)
                        if src not in seen:
                            result["images"].append(src)
                            seen.add(src)
                if result["images"]:
                    break
    except Exception:
        pass

    try:
        specs = await extract_specs_from_table(page)
        result["specs"] = specs
    except Exception:
        pass

    try:
        availability_loc = page.locator("div:has-text('в наявності'), div:has-text('Немає в наявності'), span:has-text('в наявності'), span:has-text('Немає в наявності')")
        if await availability_loc.count():
            result["availability"] = (await availability_loc.first.inner_text()).strip()
        else:
            body_text = await page.content()
            if "в наявності" in body_text:
                result["availability"] = "в наявності"
            elif "немає в наявності" in body_text.lower():
                result["availability"] = "немає в наявності"
    except Exception:
        pass

    try:
        if await page.locator(".rating, .product-rating, .rate-stars").count():
            result["rating"] = (await page.locator(".rating, .product-rating, .rate-stars").first.inner_text()).strip()
        # reviews count
        reviews_loc = page.locator("text=відгук, text=відгуків, text=відгуків:")
        if await reviews_loc.count():
            result["reviews_count"] = (await reviews_loc.first.inner_text()).strip()
        else:
            body = await page.inner_text("body")
            m = re.search(r"(\d+)\s+відгук", body)
            if m:
                result["reviews_count"] = m.group(1)
    except Exception:
        pass

    return result


async def init_context_stealth(browser: Browser) -> BrowserContext:
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1536, "height": 864},
        locale="uk-UA",
        java_script_enabled=True,
    )

    await context.add_init_script(
        """
        // Hide webdriver flag
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        // Mock plugins and languages
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['uk-UA','uk','en-US','en']});
        // Pass Chrome test
        window.chrome = { runtime: {} };
        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.__proto__.query = function(parameters) {
            if (parameters && parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery.apply(this, arguments);
        };
        """
    )
    return context


def save_results(results: List[Dict]):
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[+] JSON saved to {OUTPUT_JSON}")
    except Exception as e:
        print("[!] Could not save JSON:", e)

    try:
        keys = ["url", "title", "sku", "price", "old_price", "images", "specs", "availability", "rating", "reviews_count", "error"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in results:
                row = {k: r.get(k) for k in keys}
                row["images"] = json.dumps(row["images"], ensure_ascii=False)
                row["specs"] = json.dumps(row["specs"], ensure_ascii=False)
                writer.writerow(row)
        print(f"[+] CSV saved to {OUTPUT_CSV}")
    except Exception as e:
        print("[!] Could not save CSV:", e)


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,
                                         args=[
                                             "--disable-blink-features=AutomationControlled",
                                             "--no-sandbox",
                                             "--disable-dev-shm-usage",
                                         ])
        try:
            context = await init_context_stealth(browser)
            page = await context.new_page()

            await page.set_extra_http_headers(
                {"Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"}
            )

            for url in URLS:
                print(f"[+] Парсимо: {url}")
                try:
                    parsed = await parse_product(page, url)
                    results.append(parsed)
                    print("[+] Parsed:", parsed.get("title") or parsed.get("error"))
                except Exception as e:
                    print("[!] Error parsing", url, e)
                    results.append({"url": url, "error": str(e)})
                await asyncio.sleep(1.0)

            await context.close()
        finally:
            await browser.close()

    save_results(results)
    print("[*] Готово.")


if __name__ == "__main__":
    asyncio.run(main())
