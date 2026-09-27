from datetime import timedelta
from pathlib import Path
from typing import Any

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent


environ.Env.read_env(BASE_DIR / '.env.local')

env = environ.Env()

# Safe defaults, so the project can run on a clean system without .env.local.
# Real values must be overridden in production (see prod.py).
SECRET_KEY = env('SECRET_KEY', default='django-insecure-local-dev-key')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Shop identity
SHOP_NAME = env('SHOP_NAME', default='Brew & Barrel')
SHOP_CURRENCY = env('SHOP_CURRENCY', default='USD')

# Email notifications (Resend REST API)
RESEND_API_KEY = env('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = env('RESEND_FROM_EMAIL', default='orders@example.com')
# Admin copy of order confirmations; empty disables the copy.
SHOP_EMAIL = env('SHOP_EMAIL', default='')

# Reverse proxies (nginx/Caddy/Traefik) and their networks. X-Forwarded-For is
# only honoured when the immediate peer is listed here, otherwise a client could
# mint a fresh rate-limit bucket per request. Leave empty when there is no proxy.
TRUSTED_PROXY_IPS = env.list('TRUSTED_PROXY_IPS', default=[])

# Credential POSTs to the storefront and admin login, enforced by
# apps.core.middleware.LoginThrottleMiddleware.
LOGIN_ATTEMPT_RATE = env('LOGIN_ATTEMPT_RATE', default='10/min')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    # apps
    'apps.accounts',
    'apps.api',
    'apps.catalog',
    'apps.core',
    'apps.orders',
    'apps.payments',
    'apps.reviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # csp.middleware.CSPMiddleware adds the header; keep it near the top so a
    # redirect or error response still carries it.
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # After CSRF on purpose: a request without a valid token is rejected before
    # it can consume a rate-limit slot.
    'apps.core.middleware.LoginThrottleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'apps.core.context_processors.main_context',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
if DATABASE_URL := env('DATABASE_URL', default=None):
    DATABASES = {'default': env.db('DATABASE_URL')}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profile'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGES = [
    ('en', 'English'),
    ('uk', 'Українська'),
]

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


REST_FRAMEWORK: dict[str, Any] = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Rate limits, tunable per environment. Views opt into a stricter scope with
    # `throttle_scope` (see apps/api/views.py); ScopedRateThrottle ignores views
    # without a scope, so listing it here is safe.
    'DEFAULT_THROTTLE_CLASSES': (
        # Client-IP aware subclasses: behind a reverse proxy the stock throttles
        # would key on the proxy address and share one bucket between all users.
        'apps.core.throttling.ClientIpAnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'apps.core.throttling.ClientIpScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('DRF_THROTTLE_ANON', default='120/min'),
        'user': env('DRF_THROTTLE_USER', default='600/min'),
        'login': env('DRF_THROTTLE_LOGIN', default='10/min'),
        'register': env('DRF_THROTTLE_REGISTER', default='20/hour'),
    },
    'PAGE_SIZE': 12,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# --- Content Security Policy -------------------------------------------------
# django-csp 4.0 configures the policy through a single settings dict.
# It lives in base.py rather than prod.py so violations surface in development
# too. The third-party origins and the inline-style exception are deliberate:
# Google Fonts and FontAwesome load from CDNs, and several templates set style
# attributes inline. script-src stays strict — no inline handlers, no eval.
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        'script-src': ["'self'"],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'https://fonts.googleapis.com',
            'https://cdnjs.cloudflare.com',
        ],
        'font-src': ["'self'", 'https://fonts.gstatic.com'],
        'img-src': ["'self'", 'data:'],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
        'frame-ancestors': ["'none'"],
    },
    # Django admin ships three inline <script> blocks of its own, so it is
    # excluded instead of weakening script-src for the whole site.
    'EXCLUDE_URL_PREFIXES': ['/admin'],
}

SPECTACULAR_SETTINGS = {
    'TITLE': f'{SHOP_NAME} API',
    'DESCRIPTION': f'REST API for the {SHOP_NAME} shop: products, orders, cart, reviews and JWT auth.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
