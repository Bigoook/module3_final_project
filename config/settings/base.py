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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
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
LOGIN_URL = '/login/'
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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


REST_FRAMEWORK: dict[str, Any] = {}
