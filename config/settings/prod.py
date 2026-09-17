"""Production settings (config.settings.prod).

Every sensitive value must come from the environment (via .env / Docker).
"""

from .base import *

DEBUG = False
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
DATABASES = {'default': env.db('DATABASE_URL')}
