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

## Перевірки

```powershell
.\.venv\Scripts\ruff.exe check apps/
.\.venv\Scripts\ruff.exe format --check apps/ config/ manage.py
.\.venv\Scripts\python.exe -m mypy apps
.\.venv\Scripts\python.exe -m pytest -q
```
