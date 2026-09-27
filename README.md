# module3_final_project

## Мови та URL

Магазин двомовний: **EN** (за замовчуванням) і **UA**. Мова визначається префіксом URL:

| Сторінка        | English            | Українська              |
| --------------- | ------------------ | ----------------------- |
| Головна         | `/`                | `/uk/`                  |
| Продукти        | `/products/`       | `/uk/products/`         |
| Картка продукту | `/products/<slug>/`| `/uk/products/<slug>/`  |
| Кошик           | `/cart/`           | `/uk/cart/`             |
| Оформлення      | `/checkout/`       | `/uk/checkout/`         |
| Мої замовлення  | `/orders/`         | `/uk/orders/`           |

Технічні ендпоїнти лишаються без префікса: `/admin/`, `/health/`, `/api/`, `/api/schema/`, `/api/docs/`.
Перемикач `EN | UA` у шапці зберігає поточну сторінку та query string.

## Робота з перекладами

Джерельні рядки — англійською; переклади — у `locale/uk/LC_MESSAGES/django.po`.

```powershell
# gettext має бути в PATH (Windows)
$env:PATH = "C:\Program Files\gettext-iconv\bin;$env:PATH"

.venv\Scripts\python.exe manage.py makemessages -l uk
# ...заповнити msgstr у django.po...
.venv\Scripts\python.exe manage.py compilemessages -l uk
```

- `*.mo` у `.gitignore`, тому `compilemessages` треба виконувати після deploy/оновлення — інакше зміни не видно. Потрібен пакет **gettext** (`msgfmt`): у CI та в `docker-entrypoint.sh` він встановлюється/компілюється автоматично, а `conftest.py` перед тестами збирає `.mo`, якщо вони застаріли або відсутні.
- Нові рядки: `{% translate %}` / `{% blocktranslate %}` у шаблонах, `gettext` / `gettext_lazy` у Python; інтерполяція — лише іменовані плейсхолдери `%(name)s`.
- Назви товарів і категорій — дані БД, вони лишаються англійською в обох мовах.
- Листи про замовлення рендеряться без request, тому за замовчуванням надсилаються англійською; щоб додати іншу мову листа, потрібно зберігати мову користувача і активувати її через `translation.override`.
- **Адмінка (`/admin/`) — тільки англійською.** Вона не має мовного префікса, тож `LocaleMiddleware` для неї завжди активує `LANGUAGE_CODE = 'en'`. Тому її рядки свідомо **не** обгорнуті в `gettext`/`{% translate %}` і не потрапляють у `django.po` — інакше в `.po` були б переклади, яких ніколи не видно. Якщо захочеш двомовну адмінку, спершу додай їй префікс мови, і тільки потім повертай переклади.

## Обмеження запитів API

Усі ендпоїнти REST обмежені за частотою (DRF throttling), ліміти задаються в `config/settings/base.py`
і перекриваються змінними оточення:

| Scope | Змінна | Типовий ліміт | Що захищає |
| --- | --- | --- | --- |
| `anon` | `DRF_THROTTLE_ANON` | `120/min` | публічні `GET` без токена |
| `user` | `DRF_THROTTLE_USER` | `600/min` | запити авторизованого клієнта |
| `login` | `DRF_THROTTLE_LOGIN` | `10/min` | `/api/users/login/`, `/api/users/refresh/` — перебір паролів |
| `register` | `DRF_THROTTLE_REGISTER` | `20/hour` | `/api/users/register/` — спам-акаунти |

Перевищення → `429 Too Many Requests` з заголовком `Retry-After`. Вьюха підключає scope через
`throttle_scope` (`apps/api/views.py`); `ScopedRateThrottle` ігнорує вьюхи без scope, тож решта
ендпоінтів лімітується за `anon`/`user`.

### Лічильники мають бути спільними для всіх воркерів

Ліміти живуть у кеші Django. Стандартний `LocMemCache` належить **одному процесу**, а gunicorn
запускає кілька (`GUNICORN_WORKERS`) — кожен воркер вів би власний рахунок, і реальний ліміт
виявився б у N разів більшим за налаштований. Тому в `config/settings/prod.py` кеш замінено на
файловий у спільному каталозі (`CACHE_DIR`), який бачать усі воркери. Коли застосунок переїде
більше ніж на один хост — замінити на Redis.

### X-Forwarded-For і довіра до проксі

За проксі (nginx/Caddy/Traefik) у `REMOTE_ADDR` стоїть адреса проксі, тому stock-throttle бачив би
всіх відвідувачів як одного користувача: один зловмисник міг би заблокувати логін усім. Власні
класи в `apps/core/throttling.py` беруть адресу через `apps/core/clientip.py`, яка читає
`X-Forwarded-For` **лише** коли безпосередній peer перелічений у `TRUSTED_PROXY_IPS`
(IP або CIDR, через кому). Без цієх значень заголовок ігнорується — інакше клієнт міг би підробляти
новий ліміт щоразу. Заповни `TRUSTED_PROXY_IPS` у `.env.prod` перед деплоєм.

### Логін і адмінка

DRF-throttle не бачать звичайні Django-в'юхи, тому `/accounts/login/` і `/admin/login/` захищає
`apps.core.middleware.LoginThrottleMiddleware`: `LOGIN_ATTEMPT_RATE` (типово `10/min`) на POST
із credentials, `429` з `Retry-After` понад ліміт. `GET` сторінки форми не лімітується, щоб
перезавантаження не блокувало реальну людину.

## Content-Security-Policy

`CONTENT_SECURITY_POLICY` у `config/settings/base.py` (працює і в dev, щоб порушення were
видимі одразу). `script-src 'self'` — без інлайн-обробників, `eval` і сторонніх скриптів;
`object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`.

Два винятки свідомі:

- `style-src` містить `'unsafe-inline'` і CDN Google Fonts / FontAwesome — у шаблонах є
  інлайн-`style="..."`, а шрифти підвантажуються з `fonts.googleapis.com` / `cdnjs.cloudflare.com`.
  Скрипти при цьому залишаються суворими.
- `/admin` виключено через `EXCLUDE_URL_PREFIXES`: Django admin містить три власні інлайн-`<script>`,
  тож або виключити його, або послабити `script-src` для всього сайту.

## Перевірки

```powershell
.\.venv\Scripts\ruff.exe check apps/
.\.venv\Scripts\ruff.exe format --check apps/ config/ manage.py
.\.venv\Scripts\python.exe -m mypy apps
.\.venv\Scripts\python.exe -m pytest -q
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
  `docker-entrypoint.sh` втратить права писати `.mo` у `locale/`, а локальний dev з Linux_bind-mounts може зламатись.
