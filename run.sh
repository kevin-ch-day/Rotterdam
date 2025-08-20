#!/usr/bin/env bash
# =============================================================================
# run.sh — Rotterdam launcher (menu-driven CLI by default)
#
# Fresh install workflow:
#   1) ./setup.sh     # create .venv, install system + python deps
#   2) ./run.sh       # launches main menu via `python main.py`
#
# Why this script:
# - Always run from repo root (no CWD surprises)
# - Auto-run setup.sh if .venv is missing (or use --setup / --setup-only)
# - Source default WEB HOST/PORT from server/serv_config.py for consistency
# - Add diagnostics (--check) to catch common issues early
# - Keep behavior simple: this script launches the CLI menu (python main.py)
#
# NOTE: The web server is launched from inside the CLI (e.g., menu option [5]).
#       We export APP_HOST/APP_PORT/PORT so that server code can bind correctly.
# =============================================================================

set -euo pipefail

# ----------------------------- Pretty logging -------------------------------
OK="[OK]"; WARN="[!]"; ERR="[X]"; INF="[*]"
note(){ echo "${INF} $*"; }
good(){ echo "${OK} $*"; }
warn(){ echo "${WARN} $*"; }
fail(){ echo "${ERR} $*"; exit 1; }

# --------------------------- Resolve repository root ------------------------
# Works even if run via symlink or from another directory.
# Fixes earlier IndexError by passing argv properly to python -c.
resolve_path() {
  local p="$1"
  if command -v readlink >/dev/null 2>&1; then
    # -f resolves symlinks to an absolute path (preferred on Fedora)
    readlink -f "$p" 2>/dev/null || python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$p"
  else
    python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$p"
  fi
}
# Use $0 so it's robust even if someone invokes with sh; shebang still prefers bash.
SCRIPT_PATH="$(resolve_path "$0")"
ROOT_DIR="$(dirname "$SCRIPT_PATH")"
cd "$ROOT_DIR"

# ------------------------------ Default settings ---------------------------
# Source defaults from server/serv_config.py to avoid divergence.
APP_HOST_DEFAULT="$(python - <<'PY'
from server.serv_config import DEFAULT_HOST
print(DEFAULT_HOST)
PY
)"
APP_PORT_DEFAULT="$(python - <<'PY'
from server.serv_config import DEFAULT_PORT
print(DEFAULT_PORT)
PY
)"

# ------------------------------- CLI options --------------------------------
RUN_SETUP=0
SETUP_ONLY=0
DO_CHECK=0
APP_HOST="$APP_HOST_DEFAULT"
APP_PORT="$APP_PORT_DEFAULT"
CLI_ARGS=()

usage() {
  cat <<EOF
Usage: ./run.sh [OPTIONS] [-- <cli args>]

Launch the Rotterdam interactive CLI (menu). Any arguments after '--'
are passed directly to python main.py (e.g., --json).

Options:
  --setup            Run setup.sh before launching
  --setup-only       Run setup.sh and exit
  --check            Run basic diagnostics and exit

  --host <ip>        Host to bind for web server (default: ${APP_HOST_DEFAULT})
  --port <port>      Port to bind for web server (default: ${APP_PORT_DEFAULT})

  -h, --help         Show this help message

Notes:
- This script launches: python main.py
- The Web/UI is typically started from within the CLI (e.g., menu option [5]).
- Host/port are exported as APP_HOST/APP_PORT/PORT for the server to use.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup) RUN_SETUP=1; shift ;;
    --setup-only) RUN_SETUP=1; SETUP_ONLY=1; shift ;;
    --check) DO_CHECK=1; shift ;;
    --host)
      [[ $# -ge 2 ]] || fail "Missing value for --host"
      APP_HOST="$2"; shift 2 ;;
    --port)
      [[ $# -ge 2 ]] || fail "Missing value for --port"
      APP_PORT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; CLI_ARGS+=("$@"); break ;;
    *) CLI_ARGS+=("$1"); shift ;;
  esac
done

# ------------------------------ Helpers -------------------------------------
ensure_python() {
  if ! command -v python >/dev/null 2>&1; then
    fail "Python not found in PATH"
  fi
  # Optional: enforce minimum Python version if your project needs it (e.g., 3.10+)
  python - <<'PY' || { echo "[X] Python 3.10+ required" >&2; exit 1; }
import sys
maj, min = sys.version_info[:2]
sys.exit(0 if (maj>3 or (maj==3 and min>=10)) else 1)
PY
}

diagnostics() {
  echo "---- Diagnostics ----"
  echo "Repo root:      $ROOT_DIR"
  echo "Python:         $(command -v python || echo 'missing')"
  echo "Pip:            $(command -v pip || echo 'missing')"
  echo "Virtualenv:     $([[ -d .venv ]] && echo 'present' || echo 'MISSING')"
  echo "Main entry:     $([[ -f main.py ]] && echo 'main.py found' || echo 'MISSING main.py')"
  echo "UI index:       $([[ -f ui/pages/index.html ]] && echo 'present' || echo 'MISSING')"
  echo "ADB:            $(command -v adb || echo 'missing')"
  echo "Host/Port:      ${APP_HOST}:${APP_PORT}"
  echo "---------------------"
}

# --------------------------- Optional: diagnostics ---------------------------
if [[ $DO_CHECK -eq 1 ]]; then
  diagnostics
  exit 0
fi

# ------------------------------ Setup / venv --------------------------------
maybe_setup() {
  if [[ $RUN_SETUP -eq 1 || ! -d .venv ]]; then
    note "Running setup.sh..."
    [[ -x ./setup.sh ]] || fail "setup.sh is missing or not executable."
    ./setup.sh || { status=$?; fail "setup.sh failed with status $status"; }
    [[ $SETUP_ONLY -eq 1 ]] && { good "Setup complete (--setup-only)."; exit 0; }
  fi
}
maybe_setup

# Ensure the virtual environment exists (setup.sh should have created it).
[[ -f .venv/bin/activate ]] || fail "Virtual environment not found. Run ./setup.sh first."
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

# Check python version now that venv is active
ensure_python

# ---------------------------- Export runtime env ----------------------------
# These are read by the server when the CLI launches the web app (menu option).
export APP_HOST="${APP_HOST}"
export APP_PORT="${APP_PORT}"
# Provide a generic PORT for frameworks/tools that expect it.
export PORT="${APP_PORT}"

note "Environment:"
note "  APP_HOST=${APP_HOST}"
note "  APP_PORT=${APP_PORT}"
good "Launching Rotterdam menu (python main.py)..."

# ------------------------------ Launch the CLI ------------------------------
# main.py: top-level entry that runs the interactive menu. It accepts --json.
exec python main.py "${CLI_ARGS[@]}"
