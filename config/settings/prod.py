"""Production settings (config.settings.prod).

Every sensitive value must come from the environment, which docker-compose.prod.yml
populates from .env.prod. Activate with DJANGO_SETTINGS_MODULE=config.settings.prod.
"""

import tempfile
from pathlib import Path

from .base import *

DEBUG = False
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
DATABASES = {'default': env.db('DATABASE_URL')}

# --- Shared cache ------------------------------------------------------------
# Rate limits live in the cache, and Django's default LocMemCache is per-process.
# Gunicorn runs several workers, so each would keep its own counter and the
# effective limit would be multiplied by the worker count. A file-based cache in
# a shared directory gives every worker (and every container on one host) the
# same counters without adding a Redis service. Swap in Redis when the app runs
# on more than one host.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        # Resolved at run time rather than hardcoded: a dedicated subdirectory of
        # the system temp dir, overridable with CACHE_DIR.
        'LOCATION': env('CACHE_DIR', default=str(Path(tempfile.gettempdir()) / 'django-cache')),
    }
}

# --- Static files ---------------------------------------------------------
# In production Django no longer serves static files, so WhiteNoise takes over.
# Its docs ask for the middleware right after SecurityMiddleware, which is
# MIDDLEWARE[0] in base.py.
MIDDLEWARE = [MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE[1:]]
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# --- HTTPS / cookies ------------------------------------------------------
# Defaults assume the app runs behind a TLS-terminating proxy, which is why
# SECURE_PROXY_SSL_HEADER is set. Turn individual switches off with env vars
# when the app is served over plain HTTP (e.g. behind a local tunnel).
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
# Scheme + host of the public site, e.g. https://shop.example.com
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# --- Logging --------------------------------------------------------------
# Containers must log to stdout, not to a file inside the container.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', default='INFO'),
    },
}
