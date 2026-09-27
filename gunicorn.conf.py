"""Gunicorn config for production (config.settings.prod).

Values come from the container environment, so `env_file: .env.prod` in
docker-compose.prod.yml is enough to tune them. Note that `${VAR}`
interpolation inside a compose file reads the *host* environment instead,
which is why the tuning lives here.

Run locally to check the resolved config:

    gunicorn --config gunicorn.conf.py --print-config
"""

import multiprocessing
import os

bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
threads = int(os.environ.get('GUNICORN_THREADS', '1'))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '60'))
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', '5'))

# Log to stdout/stderr so `docker compose logs` shows everything.
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('DJANGO_LOG_LEVEL', 'info').lower()
