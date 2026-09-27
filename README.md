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

## Мови та URL

Магазин двомовний: **EN** (за замовчуванням) і **UA**. Мова визначається префіксом URL:

| Сторінка | English | Українська |
| --- | --- | --- |
| Головна | `/` | `/uk/` |
| Продукти | `/products/` | `/uk/products/` |
| Категорія | `/category/<slug>/` | `/uk/category/<slug>/` |
| Картка продукту | `/products/<slug>/` | `/uk/products/<slug>/` |
| Кошик | `/cart/` | `/uk/cart/` |
| Оформлення | `/checkout/` | `/uk/checkout/` |
| Мої замовлення | `/orders/` | `/uk/orders/` |
| Вхід | `/login/` | `/uk/login/` |
| Реєстрація | `/register/` | `/uk/register/` |
| Профіль | `/account/` | `/uk/account/` |
| Зміна пароля | `/account/password/` | `/uk/account/password/` |

Технічні ендпоїнти лишаються без мовного префікса:

| Ендпоїнт | URL |
| --- | --- |
| Адмінка | `/admin/` |
| Перевірка стану | `/health/` |
| REST API | `/api/` |
| Схема OpenAPI | `/api/schema/` |
| Документація Swagger | `/api/docs/` |

Перемикач `EN | UA` у шапці зберігає поточну сторінку та query string.

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

1. Забрати код з GitHub:

   ```bash
   git clone git@github.com:Bigoook/module3_final_project.git
   cd module3_final_project
   ```

2. Створити віртуальне оточення й встановити залежності:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. Налаштувати оточення:

   ```powershell
   # gettext має бути у PATH (Windows)
   $env:PATH = "C:\Program Files\gettext-iconv\bin;$env:PATH"

   # Локальні налаштування
   copy .env.example .env.local
   # заповнити DATABASE_URL, SECRET_KEY тощо
   ```

4. Приготувати базу й переклади:

   ```powershell
   python manage.py migrate
   python manage.py compilemessages -l uk
   ```

5. Заповнити демо-даними (опційно). Сівання виконується вручну — локально воно не
   автоматичне, на відміну від Docker dev, де `SEED_DATA=1`:

   ```powershell
   python manage.py seed_data      # демо-товари, користувачі, відгуки
   python manage.py setup_roles    # ролі для адмінки
   ```

6. Запустити сервер:

   ```powershell
   python manage.py runserver
   ```

### Продакшн

Потрібен чистий Linux-сервер із Docker. Прод-стенд запускає gunicorn за тим самим
`Dockerfile`, що й dev, але з `docker-compose.prod.yml` (`command:`, а не `CMD` у образі) —
тож локальна розробка з `runserver` і autoreload не зачіпається. Статику віддає
WhiteNoise, міграції й `collectstatic` виконує `docker-entrypoint.sh`.

1. Встановити Docker і Docker Compose:

   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-plugin
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. Забрати код на сервер. 

   ```bash
   git clone git@github.com:Bigoook/module3_final_project.git
   cd module3_final_project
   ```

3. Створити `.env.prod` і заповнити реальними значеннями:

   ```bash
   cp .env.prod.example .env.prod

   Згенерувати `SECRET_KEY` (будь-які 50+ випадкових символів):

   ```bash
   openssl rand -base64 50
   ```

4. Підняти стек (міграції, переклади й `collectstatic` виконує `docker-entrypoint.sh`):

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Перевірити:

   ```bash
   docker compose -f docker-compose.prod.yml ps       # db healthy, web running
   curl http://127.0.0.1:8000/health/                 # 200
   docker compose -f docker-compose.prod.yml logs -f web
   ```

6. Створити суперкористувача (бо `SEED_DATA=0`, демо-адміна немає):

   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

7. Поставити проксі з TLS перед `127.0.0.1:8000` (nginx/Caddy). Django сам сертифікати
   не бере — без проксі сайт недоступний ззовні, а HTTPS-налаштування не спрацюють.

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

### Налаштування Resend (листи про замовлення)

1. Зареєструйся на https://resend.com і створи API-ключ (Settings → API Keys).
2. Підтверди домен у Resend і вкажи його в `RESEND_FROM_EMAIL`
   (наприклад `orders@shop.example.com`). Без підтвердженого домена листи
   не відимуться — крім тестового адреса `onboarding@resend.dev`, який надсилає
   лише на email, з якого зареєстровано акаунт.
3. У `.env.prod`:

   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxx
   RESEND_FROM_EMAIL=orders@shop.example.com
   SHOP_EMAIL=shop@example.com   # копія магазину; порожнє = без копії
   ```

4. Перевірка: оформи замовлення й подивись лог — без ключа або з хибним доменом
   у консолі буде warning від `apps/core/emailing.py`.

`RESEND_FROM_EMAIL` має бути **підтвердженим відправником** у Resend, інакше API
відповідає 422. Це найчастіша причина, чому «листів немає».

## 9. Чек-ліст перед здачею

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
