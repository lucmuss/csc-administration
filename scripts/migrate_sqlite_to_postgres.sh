#!/usr/bin/env bash
set -euo pipefail

# Migrates application data from local SQLite (db.sqlite3) into PostgreSQL.
# Requirements:
# - PostgreSQL reachable (e.g. via `docker compose up -d db`)
# - Django deps installed in .venv

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-./.venv/bin/python}"
MANAGE="${PYTHON_BIN} src/manage.py"
FIXTURE_PATH="${FIXTURE_PATH:-/tmp/csc_sqlite_export.json}"
PG_HOST="${DATABASE_HOST:-${DB_HOST:-localhost}}"
PG_PORT="${DATABASE_PORT:-${DB_PORT:-${POSTGRES_HOST_PORT:-5434}}}"
PG_NAME="${DATABASE_NAME:-${DB_NAME:-${POSTGRES_DB:-csc}}}"
PG_USER="${DATABASE_USER:-${DB_USER:-${POSTGRES_USER:-csc}}}"
PG_PASSWORD="${DATABASE_PASSWORD:-${DB_PASSWORD:-${POSTGRES_PASSWORD:-csc}}}"

SQLITE_FILE="${SQLITE_FILE:-$ROOT_DIR/db.sqlite3}"
if [[ ! -f "$SQLITE_FILE" ]]; then
  echo "SQLite file not found: $SQLITE_FILE"
  exit 1
fi

echo "[1/5] Exporting data from SQLite -> $FIXTURE_PATH"
if ! USE_SQLITE=1 USE_SQLITE_FOR_TESTS=0 \
  $MANAGE dumpdata \
  --natural-foreign --natural-primary \
  --exclude auth.permission \
  --exclude contenttypes \
  --exclude sessions \
  --indent 2 > "$FIXTURE_PATH"; then
  echo "Full dump failed (likely legacy schema drift). Falling back to core app export..."
  USE_SQLITE=1 USE_SQLITE_FOR_TESTS=0 \
    $MANAGE dumpdata \
    accounts core members inventory orders compliance finance participation messaging governance audit \
    --natural-foreign --natural-primary \
    --exclude auth.permission \
    --exclude contenttypes \
    --exclude sessions \
    --indent 2 > "$FIXTURE_PATH"
fi

echo "[2/5] Running migrations on PostgreSQL"
USE_SQLITE=0 USE_SQLITE_FOR_TESTS=0 \
DATABASE_HOST="$PG_HOST" DATABASE_PORT="$PG_PORT" DATABASE_NAME="$PG_NAME" DATABASE_USER="$PG_USER" DATABASE_PASSWORD="$PG_PASSWORD" \
  $MANAGE migrate --noinput

echo "[2.5/5] Flushing PostgreSQL target database before import"
USE_SQLITE=0 USE_SQLITE_FOR_TESTS=0 \
DATABASE_HOST="$PG_HOST" DATABASE_PORT="$PG_PORT" DATABASE_NAME="$PG_NAME" DATABASE_USER="$PG_USER" DATABASE_PASSWORD="$PG_PASSWORD" \
  $MANAGE flush --noinput

echo "[3/5] Loading SQLite export into PostgreSQL"
USE_SQLITE=0 USE_SQLITE_FOR_TESTS=0 \
DATABASE_HOST="$PG_HOST" DATABASE_PORT="$PG_PORT" DATABASE_NAME="$PG_NAME" DATABASE_USER="$PG_USER" DATABASE_PASSWORD="$PG_PASSWORD" \
  $MANAGE loaddata "$FIXTURE_PATH"

echo "[4/5] Verifying Django system checks"
USE_SQLITE=0 USE_SQLITE_FOR_TESTS=0 \
DATABASE_HOST="$PG_HOST" DATABASE_PORT="$PG_PORT" DATABASE_NAME="$PG_NAME" DATABASE_USER="$PG_USER" DATABASE_PASSWORD="$PG_PASSWORD" \
  $MANAGE check

echo "[5/5] Done."
echo "PostgreSQL migration completed successfully."
