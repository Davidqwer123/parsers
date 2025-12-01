Product Parsers

Цей репозиторій містить три парсери для збору інформації про товари з сайту brain.com.ua.
Кожен парсер використовує різні підходи: Selenium, Playwright та Requests + BeautifulSoup.
Дані можна зберігати у PostgreSQL або у файли JSON/CSV.

Парсери
1. Selenium Parser

Використовує Selenium для відкриття сторінки та збору даних.

Отримує:

Назву товару

Колір

Обсяг пам’яті

Виробника

Ціну та знижкову ціну

Зображення

SKU

Кількість відгуків

Діагональ та роздільну здатність екрану

Специфікації

Зберігає дані у PostgreSQL.

2. Playwright Parser

Використовує Playwright (асинхронно) для парсингу.

Імітує дії користувача, щоб сайт не блокував скрипт.

Збирає ті ж дані, що й Selenium-парсер.

Зберігає результат у JSON та CSV файли.

Підходить для масштабного та швидкого парсингу багатьох сторінок.

3. Requests + BeautifulSoup Parser

Використовує requests для отримання HTML та BeautifulSoup для парсингу.

Парсить:

Назву

Колір

Пам’ять

Виробника

Ціни

Зображення

SKU

Відгуки

Екран

Специфікації

Зберігає дані у PostgreSQL.

Простий і легкий для швидких завдань без браузера.

Вимоги

Python 3.9+

Бібліотеки:

selenium
beautifulsoup4
playwright
psycopg2
webdriver-manager


PostgreSQL для збереження даних.

Google Chrome для Selenium.

Як запускати
Selenium Parser
python selenium_parser.py

Playwright Parser
python playwright_parser.py

Requests + BeautifulSoup Parser
python requests_parser.py

База даних PostgreSQL

Приклад таблиці products:

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    full_name TEXT,
    color TEXT,
    memory TEXT,
    vendor TEXT,
    price TEXT,
    price_sale TEXT,
    images JSON,
    sku TEXT,
    reviews_count INTEGER,
    screen_diagonal TEXT,
    screen_resolution TEXT,
    specifications JSON
);

Результат

Дані зберігаються у PostgreSQL або у JSON/CSV (для Playwright).

Парсери дозволяють швидко отримувати інформацію про товари для аналізу чи додаткових сервісів.
