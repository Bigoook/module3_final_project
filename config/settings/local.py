"""Local development settings (config.settings.local).

Default for manage.py, pytest and CI. Uses SQLite unless DATABASE_URL is set.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']
