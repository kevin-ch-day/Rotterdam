#!/usr/bin/env bash
# File: run.sh
set -euo pipefail

OK="[OK]"; WARN="[!]"; ERR="[X]"; INF="[*]"
note(){ echo "${INF} $*"; }
good(){ echo "${OK} $*"; }
warn(){ echo "${WARN} $*"; }
fail(){ echo "${ERR} $*"; exit 1; }

# Resolve repository root even if invoked via symlink
resolve_path() {
  local p="$1"
  if command -v readlink >/dev/null 2>&1; then
    readlink -f "$p" 2>/dev/null || python3 - "$p" <<'PY'
import os,sys; print(os.path.realpath(sys.argv[1]))
PY
  else
    python3 - "$p" <<'PY'
import os,sys; print(os.path.realpath(sys.argv[1]))
PY
  fi
}
SCRIPT_PATH="$(resolve_path "$0")"
ROOT_DIR="$(dirname "$SCRIPT_PATH")"
cd "$ROOT_DIR"

# Load default host/port from settings package; fallback if import fails
read_defaults() {
  python3 - <<'PY' || true
try:
    from settings import get_settings
    s = get_settings()
    print(f"{s.host} {s.port}")
except Exception:
    print("127.0.0.1 8000")
PY
}
read -r APP_HOST_DEFAULT APP_PORT_DEFAULT < <(read_defaults)

# CLI options
DO_CHECK=0
APP_HOST="$APP_HOST_DEFAULT"
APP_PORT="$APP_PORT_DEFAULT"
CLI_ARGS=()

usage() {
  cat <<EOF
Usage: ./run.sh [OPTIONS] [-- <cli args>]

Launch the Rotterdam interactive CLI (python main.py).
Any args after '--' are passed directly to main.py.

Options:
  --check            Run diagnostics and exit
  --host <ip>        Host to bind for web server (default: ${APP_HOST_DEFAULT})
  --port <port>      Port to bind for web server (default: ${APP_PORT_DEFAULT})
  -h, --help         Show this help message

Notes:
- This script assumes ./setup.sh has already been run.
- The web server is typically started from inside the CLI menu.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) DO_CHECK=1; shift ;;
    --host) [[ $# -ge 2 ]] || fail "Missing value for --host"; APP_HOST="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || fail "Missing value for --port"; APP_PORT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; CLI_ARGS+=("$@"); break ;;
    *) CLI_ARGS+=("$1"); shift ;;
  esac
done

diagnostics() {
  echo "---- Diagnostics ----"
  echo "Repo root:      $ROOT_DIR"
  echo "Venv:           $([[ -d .venv ]] && echo present || echo MISSING)"
  echo "Python:         $(command -v python || echo missing)"
  echo "Main entry:     $([[ -f main.py ]] && echo found || echo MISSING)"
  echo "ADB:            $(command -v adb || echo missing)"
  echo "aapt2:          $(command -v aapt2 || echo missing)"
  echo "apktool:        $(command -v apktool || echo missing)"
  echo "Host/Port:      ${APP_HOST}:${APP_PORT}"
  echo "---------------------"
}

if [[ $DO_CHECK -eq 1 ]]; then
  diagnostics
  exit 0
fi

# Require venv prepared by setup.sh
if [[ ! -f .venv/bin/activate ]]; then
  fail "Virtual environment not found. Run ./setup.sh first."
fi

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

# Export runtime env for server
export APP_HOST="$APP_HOST"
export APP_PORT="$APP_PORT"
export PORT="$APP_PORT"

note "Environment:"
note "  APP_HOST=${APP_HOST}"
note "  APP_PORT=${APP_PORT}"
good "Launching Rotterdam menu (python main.py)..."

exec python main.py "${CLI_ARGS[@]}"
