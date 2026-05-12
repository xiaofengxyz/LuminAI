#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/vendor/jellyfish/backend"
FRONT_DIR="$ROOT_DIR/vendor/jellyfish/front"
LOG_DIR="$ROOT_DIR/.runtime/logs"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8011}"
FRONT_HOST="${FRONT_HOST:-0.0.0.0}"
FRONT_PORT="${FRONT_PORT:-7790}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:${BACKEND_PORT}}"

mkdir -p "$LOG_DIR"

# Local dev must bypass host proxies; otherwise localhost health checks can
# return proxy 502 even when uvicorn and Vite are listening correctly.
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

is_listening() {
  local port="$1"
  ss -ltn "( sport = :$port )" | awk 'NR > 1 { found=1 } END { exit found ? 0 : 1 }'
}

start_detached() {
  local work_dir="$1"
  local log_file="$2"
  shift 2
  (
    cd "$work_dir"
    # setsid keeps the dev service alive when this recovery script is launched
    # from a short-lived automation shell; nohup is the portable fallback.
    if command -v setsid >/dev/null 2>&1; then
      setsid "$@" >"$log_file" 2>&1 < /dev/null &
    else
      nohup "$@" >"$log_file" 2>&1 < /dev/null &
    fi
  )
}

if is_listening "$BACKEND_PORT"; then
  printf 'Jellyfish backend already listening on %s\n' "$BACKEND_URL"
else
  PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
  if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="python3"
  fi
  start_detached "$BACKEND_DIR" "$LOG_DIR/jellyfish-backend-${BACKEND_PORT}.log" \
    "$PYTHON_BIN" -m uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  printf 'Started Jellyfish backend on %s (log: %s)\n' "$BACKEND_URL" "$LOG_DIR/jellyfish-backend-${BACKEND_PORT}.log"
fi

if is_listening "$FRONT_PORT"; then
  printf 'Jellyfish frontend already listening on http://localhost:%s/projects\n' "$FRONT_PORT"
else
  start_detached "$FRONT_DIR" "$LOG_DIR/jellyfish-frontend-${FRONT_PORT}.log" \
    env VITE_BACKEND_URL="$BACKEND_URL" npx pnpm@9.15.9 run dev:film-core -- --host "$FRONT_HOST" --port "$FRONT_PORT"
  printf 'Started Jellyfish frontend on http://localhost:%s/projects (log: %s)\n' "$FRONT_PORT" "$LOG_DIR/jellyfish-frontend-${FRONT_PORT}.log"
fi

printf 'Health check: NO_PROXY=%s curl --noproxy "*" %s/health\n' "$NO_PROXY" "$BACKEND_URL"
