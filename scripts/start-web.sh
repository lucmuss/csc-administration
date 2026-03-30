#!/usr/bin/env bash
set -euo pipefail

python src/manage.py migrate
python src/manage.py collectstatic --noinput

if [ "${AUTO_SEED_DEMO_DATA:-0}" = "1" ]; then
  python src/manage.py seed_demo_data
fi

exec python src/manage.py runserver 0.0.0.0:8000
