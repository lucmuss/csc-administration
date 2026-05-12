#!/usr/bin/env bash
set -euo pipefail

python src/manage.py migrate
python src/manage.py collectstatic --noinput

if [ "${AUTO_SEED_DEMO_DATA:-0}" = "1" ]; then
  python src/manage.py seed_demo_data || true &
fi

# Hintergrundwartung darf den Webstart nicht blockieren.
(
  python src/manage.py apply_membership_credits || true
  python src/manage.py send_meeting_notifications || true
) &

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile - \
  --pythonpath src
