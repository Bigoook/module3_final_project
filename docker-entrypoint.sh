#!/bin/sh
# Container entrypoint: prepare the app before handing over to the CMD.
# Translations must be compiled here because *.mo is gitignored (see .gitignore),
# so a fresh image would otherwise silently fall back to English.
set -e

echo '[entrypoint] compiling translations...'
# Same as `manage.py compilemessages --locale <lang>` for every locale, plus
# --check-format so a broken %(name)s placeholder fails fast instead of at runtime.
find locale -name '*.po' -exec sh -c 'msgfmt --check-format -o "${1%.po}.mo" "$1"' _ {} \;

# Opt-in: production serves static files through WhiteNoise, which needs
# STATIC_ROOT populated. Local dev keeps Django's static handling instead.
if [ "${COLLECTSTATIC:-0}" = '1' ]; then
    echo '[entrypoint] collecting static files...'
    python manage.py collectstatic --noinput
fi

echo '[entrypoint] applying migrations...'
python manage.py migrate --noinput

# Opt-in demo data: SEED_DATA=1 (compose sets it by default for local checks).
if [ "${SEED_DATA:-0}" = '1' ]; then
    echo '[entrypoint] seeding demo data...'
    python manage.py seed_data
fi

echo "[entrypoint] starting: $*"
exec "$@"
