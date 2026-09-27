# module3_final_project

Інтернет-магазин на Django/DRF: двомовний веб-інтерфейс (EN/UA), REST API з JWT,
адмінка з аналітикою, листи про замовлення через Resend.

## Опис проєкту

Магазин продає товари з каталогу, що ділиться на вкладені категорії. Користувач
може переглядати каталог, шукати та фільтрувати товари, додавати їх у кошик,
оформлювати замовлення та залишати відгуки — але лише після покупки. Замовлення
підтверджуються листом на email. Адмінка дає аналітику продажів і керування
товарами, замовленнями, відгуками та користувачами через ролі.

**Можливості:**

- Каталог: пагінація, фільтри за категорією й ціною, пошук, сортування.
- Кошик у сесії: додавання, видалення, зміна кількості, перевірка залишків.
- Оформлення: форма з контактами, вибір способу оплати, знімок ціни на момент покупки.
- Особистий кабінет: реєстрація, вхід/вихід, історія замовлень, редагування профілю, зміна пароля.
- Відгуки: рейтинг 1–5 і коментар, один відгук на товар — після покупки.
- REST API: товари, замовлення, кошик, відгуки, реєстрація й JWT-авторизація.
- Адмінка: аналітика (виторг, топ-продукти, кількість замовлень), ролі, кастомні дії.
- Двомовність: EN (за замовчуванням) і UA через префікс URL.
- Пошта: лист про замовлення користувачу й копія магазину через Resend.

## Технології

| Шар | Технології |
| --- | --- |
| Бекенд | Django 6.1, Django REST Framework 3.18, SimpleJWT |
| База даних | PostgreSQL 17 |
| Фронтенд | Django-шаблони, CSS, JS (без фреймворків) |
| Пошта | Resend |
| Статика | WhiteNoise |
| Тестування | pytest, pytest-django, pytest-cov |
| Лінтери | ruff, mypy, django-stubs |
| Інфраструктура | Docker, Docker Compose, GitHub Actions |

## Структура проєкту

```
module3_final_project/
├── config/                 # Налаштування Django, URL, WSGI/ASGI, admin site
│   ├── settings/           # base.py, local.py, prod.py
│   ├── urls.py
│   └── admin_site.py
├── apps/
│   ├── accounts/           # Реєстрація, вхід, профіль, ролі
│   ├── api/                # REST API: views, urls, serializers
│   ├── catalog/            # Товари, категорії, фільтри, селектори
│   ├── core/               # Пошта, переклади, безпека, команди
│   ├── orders/             # Кошик, замовлення, сервіси, форми
│   ├── payments/           # Заглушка (не використовується)
│   └── reviews/            # Відгуки та їх сервіси
├── templates/              # Шаблони (catalog, orders, accounts, emails, ...)
├── static/                 # CSS, JS, зображення
├── locale/uk/LC_MESSAGES/  # Переклади (django.po)
├── conftest.py             # Фікстури pytest
├── manage.py
├── Dockerfile
├── docker-compose.yml      # Dev-стенд
├── docker-compose.prod.yml # Прод-стенд
├── requirements.txt        # Runtime-залежності
├── requirements-dev.txt    # Тестування та лінтери
├── .github/workflows/      # CI та публікація образу
└── README.md
```

Тести знаходяться в `apps/*/tests/`. Бізнес-логіка розділена на шари:
`selectors.py` (читання), `services.py` (зміни), `views.py` (HTTP).

## Встановлення та запуск

### Через Docker (рекомендовано)

```powershell
docker compose up -d --build
```

Після запуску магазин доступний на `http://127.0.0.1:8000/` (англійською) та
`http://127.0.0.1:8000/uk/` (українською). Статус перевіряється на
`http://127.0.0.1:8000/health/`.

`docker-entrypoint.sh` при старті компілює переклади, застосовує міграції та
(у dev) сіє демо-дані. Логи: `docker compose logs -f web`.

### Локально без Docker

Потрібні Python 3.12, PostgreSQL та gettext.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt

# gettext має бути у PATH (Windows)
$env:PATH = "C:\Program Files\gettext-iconv\bin;$env:PATH"

# Локальні налаштування
copy .env.example .env.local
# заповнити DATABASE_URL, SECRET_KEY тощо

python manage.py migrate
python manage.py compilemessages -l uk
python manage.py runserver
```

### Продакшн

```powershell
copy .env.prod.example .env.prod
# заповнити SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DATABASE_URL,
# POSTGRES_*, RESEND_API_KEY, TRUSTED_PROXY_IPS, CACHE_DIR; SEED_DATA=0

docker compose -f docker-compose.prod.yml up -d --build
```

Прод-стенд запускає gunicorn за тим самим `Dockerfile`, що й dev, але з
`docker-compose.prod.yml` (`command:`, а не `CMD` у образі) — тож локальна розробка
з `runserver` і autoreload не зачіпається. Статику віддає WhiteNoise, міграції й
`collectstatic` виконує `docker-entrypoint.sh`.

## Приклади використання API

Базова адреса — `http://127.0.0.1:8000`. Усі запити — JSON.

### Реєстрація

```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ivan", "email": "ivan@example.com", "password": "Strong-Pass-2026!"}'
```

Відповідь `201` — дані користувача (без пароля).

### Вхід (JWT)

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ivan", "password": "Strong-Pass-2026!"}'
```

```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```

- `access` дійсний 30 хвилин, `refresh` — 7 днів.
- Усі захищені ендпоінти вимагають заголовок `Authorization: Bearer <access>`.

### Оновлення токена

```bash
curl -X POST http://127.0.0.1:8000/api/users/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJhbGciOi..."}'
```

### Товари

```bash
# Список з пагінацією, фільтрами, пошуком і сортуванням
curl "http://127.0.0.1:8000/api/products/?search=ale&min_price=5&max_price=20&ordering=-price"

# Деталі товару (з відгуками, схожими товарами й прапорцем can_review)
curl http://127.0.0.1:8000/api/products/1/
```

Параметри списку: `search`, `category` (slug), `min_price`, `max_price`,
`in_stock`, `ordering` (`name`, `-name`, `price`, `-price`, `-rating`, `-sold`,
`-created_at`). Розмір сторінки — 12.

### Кошик

```bash
# Перегляд
curl http://127.0.0.1:8000/api/cart/ -H "Authorization: Bearer <access>"

# Додати товар
curl -X POST http://127.0.0.1:8000/api/cart/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Змінити кількість
curl -X PATCH http://127.0.0.1:8000/api/cart/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 3}'

# Видалити товар
curl -X DELETE http://127.0.0.1:8000/api/cart/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"product_id": 1}'
```

### Замовлення

```bash
# Оформити кошик (створює замовлення, знімає залишки, надсилає лист)
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ivan Petrenko",
    "email": "ivan@example.com",
    "phone": "+380501234567",
    "shipping_address": "Kyiv, Khreshchatyk 1",
    "payment_method": "card"
  }'

# Список своїх замовлень
curl http://127.0.0.1:8000/api/orders/ -H "Authorization: Bearer <access>"

# Деталі свого замовлення
curl http://127.0.0.1:8000/api/orders/1/ -H "Authorization: Bearer <access>"

# Скасувати (PATCH або DELETE)
curl -X PATCH http://127.0.0.1:8000/api/orders/1/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

Способи оплати: `card`, `cash`, `bank_transfer`. Статуси: `pending`, `paid`,
`shipped`, `delivered`, `cancelled`.

### Відгуки

```bash
# Список відгуків товару
curl http://127.0.0.1:8000/api/products/1/reviews/

# Залишити відгук (тільки після покупки цього товару)
curl -X POST http://127.0.0.1:8000/api/products/1/reviews/ \
  -H "Authorization: Bearer <access>" -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "Great taste!"}'
```

### Документація API

Swagger/OpenAPI доступний на `/api/docs/`, схема — `/api/schema/`.

## Команди для тестів та лінтерів

```powershell
# Тести
.\.venv\Scripts\python.exe -m pytest -q

# Лінтер і форматування
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .

# Перевірка типів
.\.venv\Scripts\python.exe -m mypy .

# Покриття тестами
.\.venv\Scripts\python.exe -m pytest --cov=apps --cov-report=term-missing
```

Перевірка, що продакшен-налаштування безпечні (потрібні змінні з `.env.prod`):

```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings.prod'
# Тимчасовий ключ лише для перевірки: 50+ символів, інакше Django видасть security.W009
$env:SECRET_KEY='check-only-7fK2mQ9xL4nR8tY6wB3cH5jF1sD0gA2eU7iO9mKqVxZ4pJ6hG1'
$env:ALLOWED_HOSTS='shop.example.com'
$env:DATABASE_URL='postgres://postgres:postgres@localhost:5432/final3'
.\.venv\Scripts\python.exe manage.py check --deploy
```

## Робота з перекладами

Джерельні рядки — англійською; переклади — у `locale/uk/LC_MESSAGES/django.po`.

```powershell
# gettext має бути у PATH (Windows)
$env:PATH = "C:\Program Files\gettext-iconv\bin;$env:PATH"

.\.venv\Scripts\python.exe manage.py makemessages -l uk
# ...заповнити msgstr у django.po...
.\.venv\Scripts\python.exe manage.py compilemessages -l uk
```

- `*.mo` у `.gitignore`, тому `compilemessages` треба виконувати після deploy/оновлення — інакше зміни не видно. Потрібен пакет **gettext** (`msgfmt`): у CI та в `docker-entrypoint.sh` він встановлюється/компілюється автоматично, а `conftest.py` перед тестами збирає `.mo`, якщо вони застаріли або відсутні.
- Нові рядки: `{% translate %}` / `{% blocktranslate %}` у шаблонах, `gettext` / `gettext_lazy` у Python; інтерполяція — лише іменовані плейсхолдери `%(name)s`.
- Назви товарів і категорій — дані БД, вони лишаються англійською в обох мовах.
- Листи про замовлення рендеряться без request, тому за замовчуванням надсилаються англійською; щоб додати іншу мову листа, потрібно зберігати мову користувача і активувати її через `translation.override`.
- **Адмінка (`/admin/`) — тільки англійською.** Вона не має мовного префіксу, тож `LocaleMiddleware` для неї завжди активує `LANGUAGE_CODE = 'en'`. Тому її рядки свідомо **не** обгорнуті в `gettext`/`{% translate %}` і не потрапляють у `django.po` — інакше в `.po` були б переклади, яких ніколи не видно. Якщо захочеш двомовну адмінку, спершу додай їй префікс мови, і тільки потім повертай переклади.

## Безпека

### Обмеження запитів API

Усі эндпоїнти REST обмежені за частотою (DRF throttling), ліміти задаються в `config/settings/base.py`
і перекриваються змінними оточення:

| Scope | Змінна | Типовий ліміт | Що захищає |
| --- | --- | --- | --- |
| `anon` | `DRF_THROTTLE_ANON` | `120/min` | публічні `GET` без токена |
| `user` | `DRF_THROTTLE_USER` | `600/min` | запити авторизованого клієнта |
| `login` | `DRF_THROTTLE_LOGIN` | `10/min` | `/api/users/login/`, `/api/users/refresh/` — перебір паролів |
| `register` | `DRF_THROTTLE_REGISTER` | `20/hour` | `/api/users/register/` — спам-акаунти |

Перевищення → `429 Too Many Requests` з заголовком `Retry-After`. Вьюха підключає scope через
`throttle_scope` (`apps/api/views.py`); `ScopedRateThrottle` ігнорує вьюхи без scope, тож решта
эндпоінтів лімітується за `anon`/`user`.

#### Лічильники мають бути спільними для всіх воркерів

Ліміти живуть у кеші Django. Стандартний `LocMemCache` належить **одному процесу**, а gunicorn
запускає кілька (`GUNICORN_WORKERS`) — кожен воркер вів би власний рахунок, і реальний ліміт
виявився б у N разів більшим за налаштований. Тому в `config/settings/prod.py` кеш замінено на
файловий у спільному каталозі (`CACHE_DIR`), який бачать усі воркери. Коли застосунок переїде
більше ніж на один хост — замінити на Redis.

#### X-Forwarded-For і довіра до проксі

За проксі (nginx/Caddy/Traefik) у `REMOTE_ADDR` стоїть адреса проксі, тому stock-throttle бачив би
всіх відвідувачів як одного користувача: один зловмисник міг би заблокувати логін усім. Власні
класи в `apps/core/throttling.py` беруть адресу через `apps/core/clientip.py`, яка читає
`X-Forwarded-For` **лише** коли безпосередній peer перелічений у `TRUSTED_PROXY_IPS`
(IP або CIDR, через кому). Без цих значень заголовок ігнорується — інакше клієнт міг би підробляти
новий ліміт щоразу. Заповни `TRUSTED_PROXY_IPS` у `.env.prod` перед деплоєм.

#### Логін і адмінка

DRF-throttle не бачать звичайні Django-в'юхи, тому `/accounts/login/` і `/admin/login/` захищає
`apps.core.middleware.LoginThrottleMiddleware`: `LOGIN_ATTEMPT_RATE` (типово `10/min`) на POST
із credentials, `429` з `Retry-After` понад ліміт. `GET` сторінки форми не лімітується, щоб
перезавантаження не блокувало реальну людину.

### Content-Security-Policy

`CONTENT_SECURITY_POLICY` у `config/settings/base.py` (працює і в dev, щоб порушення були
видимі одразу). `script-src 'self'` — без інлайн-обробників, `eval` і сторонніх скриптів;
`object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`.

Два винятки свідомі:

- `style-src` містить `'unsafe-inline'` і CDN Google Fonts / FontAwesome — у шаблонах є
  інлайн-`style="..."`, а шрифти підвантажуються з `fonts.googleapis.com` / `cdnjs.cloudflare.com`.
  Скрипти при цьому залишаються суворими.
- `/admin` виключено через `EXCLUDE_URL_PREFIXES`: Django admin містить три власні інлайн-`<script>`,
  тож або виключити його, або послабити `script-src` для всього сайту.

## Деплой

Прод побудований на тому ж `Dockerfile`, що й dev, але gunicorn стартує з `docker-compose.prod.yml`
(`command:`, а не `CMD` у образі) — тож локальна розробка з `runserver` і autoreload не зачіпається.

1. Підготувати оточення (значення — у `.env.prod.example`, файл `.env.prod` у git не потрапляє):

   ```powershell
   copy .env.prod.example .env.prod
   python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"  # → SECRET_KEY
   ```

2. Запустити стек (міграції, переклади й `collectstatic` виконує `docker-entrypoint.sh`):

   ```powershell
   docker compose -f docker-compose.prod.yml up -d --build
   ```

3. Перевірити: `http://127.0.0.1:8000/health/` і журнал `docker compose -f docker-compose.prod.yml logs -f web`.

**Образ публікується автоматично:** `.github/workflows/deploy.yml` збирає його й пушить у `ghcr.io` на
кожен пуш у `main` (теги `main` і `sha`). Крок на сервері лишається ручним, щоб не тягнути SSH-доступи в CI:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

**Перед продакшеном:**

- проксі з TLS перед `127.0.0.1:8000` (Django сам сертифікати не бере); у `.env.prod` — `ALLOWED_HOSTS` і `CSRF_TRUSTED_ORIGINS` з реальним доменом;
- `SEED_DATA=0` (інакше з'явиться `admin/admin12345`), `COLLECTSTATIC=1`;
- `RESEND_API_KEY` — без нього листи про замовлення пропускаються, а не надсилаються;
- бекапи БД: `pg_dump` у cron, бо `pgdata` живе у volume і зникає разом з `docker compose down -v`;
- контейнер поки що під `root`. Non-root потребує окремого `Dockerfile.prod`: з `USER` у спільному образі
  `docker-entrypoint.sh` втратить права писати `.mo` у `locale/`, а локальний dev з Linux bind-mounts може зламатись.

## 9. Вимоги до здачі проєкту

1. **Репозиторій на GitHub** — код доступний за адресою `github.com/Bigoook/module3_final_project`, використовуються гілки `main` + `feature/*`, історія комітів змістовна (8 комітів, PR #5, #6, #7).

2. **README.md** (повний, згідно п. 2 ТЗ) — містить:
   - опис проєкту;
   - інструкції зі встановлення та запуску через Docker (`docker compose up -d --build`);
   - приклади використання API з JWT (отримання токенів, `Authorization: Bearer`, оновлення);
   - команди для запуску тестів і лінтерів;
   - опис структури проєкту.

3. (Опційно) Посилання на розгорнутий проєкт або відео-демонстрація — підготовлено: образ у `ghcr.io` + інструкція `docker compose -f docker-compose.prod.yml up -d`; потрібен реальний публічний URL.

4. ПІБ, група, посилання на репозиторій — надіслано викладачеві (потрібно вставити дані).

5. **Чек-ліст реалізації** — оформлений у розділі 10 з позначками `[x]` / `[ ]`.

6. Історія комітів змістовна, гілки використовуються правильно (`feature/*` → `main` через PR).

## 10. Чек-ліст перед здачею

- [x] Проєкт запускається командою `docker compose up` на чистій системі
- [x] Використовується PostgreSQL
- [x] Каталог: реалізовано фільтри, пошук, пагінацію
- [x] Сторінка товару: є деталі, відгуки, кнопка додавання в кошик
- [x] Кошик: можна керувати вмістом, розраховується сума, є перевірка залишків
- [x] Оформлення замовлення: створюється замовлення, надсилається email, є валідація
- [x] Особистий кабінет: реєстрація, вхід, історія замовлень, редагування профілю
- [x] REST API: авторизація через JWT, документація, налаштовані права доступу
- [x] Адмін-панель: є аналітика, фільтри, зручне керування даними
- [x] Swagger/OpenAPI доступний на `/api/docs/` і коректний
- [x] Код містить типізацію та докстрінги
- [x] Лінтери проходять без критичних помилок (`ruff` — сучасний аналог `flake8` — та `mypy`)
- [x] Тести реалізовані та проходять успішно (232 тести)
- [x] README повний та зрозумілий
- [x] Коміти змістовні, гілки використовуються правильно
- [x] Цей чек-ліст додано до проєкту

### Що лишилося незакритим

- **ПІБ і група** не вказані (вимога 4).
- **Публічне посилання на деплой** відсутнє (опційна вимога 3).
- **`apps/payments/` — порожня заглушка** без моделей і view. Імітація способу оплати
  реалізована полем `Order.payment_method`; окремий застосунок не використовується.
- **Покриття тестів не вимірюється.** `pytest-cov` встановлено, але не налаштовано.
- **GraphQL не реалізовано** (бонусний пункт, на оцінку не впливає).
- **Контейнер prod працює під `root`.** Non-root потребує окремого `Dockerfile.prod`.
