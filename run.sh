#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$ROOT_DIR/web"
VENV_DIR="$ROOT_DIR/.venv"
CHECK_ONLY=false
FRESH_DB=false
OPEN_BROWSER=true
BACKEND_PID=""
FRONTEND_PID=""

usage() {
  cat <<'EOF'
Usage: ./run.sh [options]

Options:
  --check-only   Install dependencies and run validation only.
  --fresh-db     Delete the local SQLite DB before starting.
  --no-open      Do not auto-open the browser.
  --help         Show this help message.
EOF
}

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local attempts=30

  for _ in $(seq 1 "$attempts"); do
    if python3 - <<PY >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("$url", timeout=1)
PY
    then
      log "$label is ready at $url"
      return 0
    fi
    sleep 1
  done

  echo "$label did not become ready in time." >&2
  echo "Check the terminal output above for details." >&2
  exit 1
}

ensure_env_file() {
  local target_file="$1"
  local example_file="$2"

  if [[ ! -f "$target_file" ]]; then
    cp "$example_file" "$target_file"
  fi
}

load_root_env() {
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
}

validate_runtime_config() {
  local api_key="${LLM_API_KEY:-}"
  local mock_llm="${MOCK_LLM:-false}"

  if [[ "$CHECK_ONLY" == true ]]; then
    return
  fi

  if [[ -z "$api_key" && "$mock_llm" != "true" ]]; then
    cat >&2 <<EOF

run.sh stopped before starting servers.

LLM_API_KEY is empty and MOCK_LLM is false.
Set one of the following in $ROOT_DIR/.env:

  LLM_API_KEY=your_real_key
or
  MOCK_LLM=true

Then run:
  bash run.sh
EOF
    exit 1
  fi
}

cleanup() {
  local exit_code=$?

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi

  exit "$exit_code"
}

for arg in "$@"; do
  case "$arg" in
    --check-only)
      CHECK_ONLY=true
      ;;
    --fresh-db)
      FRESH_DB=true
      ;;
    --no-open)
      OPEN_BROWSER=false
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

trap cleanup EXIT INT TERM

require_command python3
require_command npm

mkdir -p "$ROOT_DIR/var/data"

if [[ "$FRESH_DB" == true ]]; then
  log "Removing local SQLite database"
  rm -f "$ROOT_DIR/var/data/home_energy.db"
fi

log "Creating local virtual environment"
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "Installing backend dependencies"
python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$ROOT_DIR/requirements.txt"

ensure_env_file "$ROOT_DIR/.env" "$ROOT_DIR/.env.example"
ensure_env_file "$WEB_DIR/.env" "$WEB_DIR/.env.example"
load_root_env
validate_runtime_config

log "Installing frontend dependencies"
cd "$WEB_DIR"
npm ci

log "Running backend tests"
cd "$ROOT_DIR"
python -m pytest -q

log "Running frontend production build"
cd "$WEB_DIR"
npm run build

if [[ "$CHECK_ONLY" == true ]]; then
  log "Check-only mode complete"
  exit 0
fi

log "Starting backend server"
cd "$ROOT_DIR"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload \
  > >(sed -u 's/^/[backend] /') \
  2> >(sed -u 's/^/[backend] /' >&2) &
BACKEND_PID=$!
wait_for_url "http://127.0.0.1:8000/docs" "Backend"

log "Starting frontend dev server"
cd "$WEB_DIR"
npm run dev -- --host 127.0.0.1 --port 5173 \
  > >(sed -u 's/^/[frontend] /') \
  2> >(sed -u 's/^/[frontend] /' >&2) &
FRONTEND_PID=$!
wait_for_url "http://127.0.0.1:5173" "Frontend"

if [[ "$OPEN_BROWSER" == true ]]; then
  if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:5173"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
  fi
fi

cat <<EOF

Home Energy Advisor is ready:
  Frontend: http://127.0.0.1:5173
  Backend docs: http://127.0.0.1:8000/docs

Press Ctrl+C to stop both servers.
EOF

wait "$BACKEND_PID" "$FRONTEND_PID"

