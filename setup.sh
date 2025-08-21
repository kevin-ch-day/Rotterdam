#!/usr/bin/env bash
# File: setup.sh
set -euo pipefail

# --- Paths ---
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs/setup"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# --- Fedora guard ---
if ! command -v dnf >/dev/null 2>&1; then
  echo "This setup script is only for Fedora (requires dnf)." >&2
  exit 1
fi

# --- Usage / flags ---
usage() {
  cat <<'EOF'
Usage: ./setup.sh [OPTIONS]

Prepare the Rotterdam environment on Fedora.
- Installs baseline system packages with dnf
- Ensures aapt2 (via scripts/install-aapt2.sh)
- Ensures apktool (via scripts/install-apktool.sh)
- Creates or updates a Python venv and installs requirements

Options:
  --force-venv   Recreate the virtual environment even if it exists
  --skip-system  Skip system package installation (dnf)
  -h, --help     Show this help message
EOF
}

FORCE_VENV=0
SKIP_SYSTEM=0
FAILED_PACKAGES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force-venv) FORCE_VENV=1; shift ;;
    --skip-system) SKIP_SYSTEM=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# --- Helpers ---
run_as_root() {
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  elif [[ ${EUID:-0} -eq 0 ]]; then
    "$@"
  else
    echo "Root privileges are required: $*" >&2
    return 1
  fi
}

LOG_FILE="$LOG_DIR/system_install.log"

# --- System packages ---
if [[ $SKIP_SYSTEM -eq 0 ]]; then
  echo "Installing system dependencies with dnf..."
  echo "Logging to: $LOG_FILE"

  packages=(python3 python3-virtualenv adb yara curl wget unzip)
  if dnf list java-21-openjdk-headless >/dev/null 2>&1; then
    packages+=(java-21-openjdk-headless)
  elif dnf list java-17-openjdk-headless >/dev/null 2>&1; then
    packages+=(java-17-openjdk-headless)
  fi

  for pkg in "${packages[@]}"; do
    echo "Installing $pkg..."
    if ! run_as_root dnf install -y "$pkg" 2>&1 | tee -a "$LOG_FILE"; then
      echo "Failed to install $pkg" | tee -a "$LOG_FILE" >&2
      FAILED_PACKAGES+=("$pkg")
    fi
  done
fi

# --- Tool installers ---
SCRIPTS_DIR="$ROOT_DIR/scripts"

if ! command -v aapt2 >/dev/null 2>&1; then
  if [[ -x "$SCRIPTS_DIR/install-aapt2.sh" ]]; then
    echo "[*] aapt2 not found - running scripts/install-aapt2.sh"
    if ! bash "$SCRIPTS_DIR/install-aapt2.sh" 2>&1 | tee -a "$LOG_FILE"; then
      echo "[X] Failed to install aapt2" | tee -a "$LOG_FILE" >&2
      FAILED_PACKAGES+=("aapt2")
    fi
  fi
fi

if ! command -v apktool >/dev/null 2>&1; then
  if [[ -x "$SCRIPTS_DIR/install-apktool.sh" ]]; then
    echo "[*] apktool not found - running scripts/install-apktool.sh"
    if ! bash "$SCRIPTS_DIR/install-apktool.sh" 2>&1 | tee -a "$LOG_FILE"; then
      echo "[X] Failed to install apktool" | tee -a "$LOG_FILE" >&2
      FAILED_PACKAGES+=("apktool")
    fi
  fi
fi

# --- Verify required tools ---
REQUIRED_CMDS=(adb yara aapt2 apktool)
missing_tools=()
for cmd in "${REQUIRED_CMDS[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required tool '$cmd' is not installed." >&2
    missing_tools+=("$cmd")
  fi
done
if ! command -v java >/dev/null 2>&1; then
  echo "Warning: 'java' not found. apktool requires Java." >&2
  missing_tools+=("java")
fi

if (( ${#missing_tools[@]} )); then
  echo "Missing tools: ${missing_tools[*]}" >&2
  exit 1
fi

# --- Python venv + deps ---
if [[ $FORCE_VENV -eq 1 && -d .venv ]]; then
  echo "Removing existing virtual environment..."
  rm -rf .venv
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing Python requirements..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Verifying installed Python packages..."
if ! python -m pip check 2>&1 | tee "$LOG_DIR/pip_check.log"; then
  echo "Dependency conflicts detected. See logs/setup/pip_check.log for details." >&2
  exit 1
fi

# --- CLI symlink ---
if [[ ! -e /usr/local/bin/rotterdam ]]; then
  run_as_root ln -sf "$ROOT_DIR/run.sh" /usr/local/bin/rotterdam
fi

# --- Ownership fix ---
if [[ -d "$ROOT_DIR/output" && -n "${SUDO_USER:-}" ]]; then
  run_as_root chown -R "$SUDO_USER":"$SUDO_USER" "$ROOT_DIR/output"
fi

echo
echo "Setup complete."
echo "Logs stored in: $LOG_DIR"
echo "Try:  rotterdam   # or ./run.sh"
