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

exec python src/manage.py runserver 0.0.0.0:8000
