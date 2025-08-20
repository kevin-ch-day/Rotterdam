#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

usage() {
    cat <<'EOF'
Usage: ./setup.sh [OPTIONS]

Prepare the Rotterdam environment on Fedora systems. Installs required
system packages, creates a Python virtual environment and pulls Python
dependencies from requirements.txt.

Options:
  --force-venv   Recreate the virtual environment even if it exists
  --skip-system  Do not install system packages with dnf
  -h, --help     Show this help message
EOF
}

FORCE_VENV=0
SKIP_SYSTEM=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force-venv) FORCE_VENV=1; shift ;;
        --skip-system) SKIP_SYSTEM=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

if ! command -v dnf >/dev/null 2>&1; then
    echo "This setup script is intended for Fedora-based systems with dnf." >&2
    exit 1
fi

if [[ ${EUID:-0} -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo "Root privileges are required to install system dependencies." >&2
        exit 1
    fi
else
    SUDO=""
fi

install_pkg() {
    local pkg="$1"
    if ! $SUDO dnf install -y "$pkg" >/dev/null 2>&1; then
        echo "Warning: package '$pkg' could not be installed. Please install it manually." >&2
        return 1
    fi
}

if [[ $SKIP_SYSTEM -eq 0 ]]; then
    echo "Installing system dependencies with dnf..."

    # Allow override via JAVA_PACKAGE (e.g., JAVA_PACKAGE=java-21-openjdk)
    JAVA_PACKAGE="${JAVA_PACKAGE:-java-17-openjdk}"

    # Resolve Java package: use requested if available, otherwise latest java-*openjdk.
    JAVA_PKG=""
    if dnf list "$JAVA_PACKAGE" >/dev/null 2>&1; then
        JAVA_PKG="$JAVA_PACKAGE"
    else
        # Find the latest available java-*openjdk
        JAVA_PKG="$(dnf list --available 'java-*openjdk' 2>/dev/null \
            | awk '/^java-[0-9]+-openjdk(\.x86_64)?\s/ {print $1}' \
            | cut -d'.' -f1 \
            | sort -t'-' -k2,2n \
            | tail -1 || true)"
        if [[ -z "$JAVA_PKG" ]]; then
            echo "Warning: no java-*openjdk package available; skipping Java installation." >&2
        fi
    fi

    # Core packages (names are Fedora-specific)
    packages=(
        python3
        python3-virtualenv
        adb
        aapt2
        apktool
        yara
    )
    # Append Java if resolved
    if [[ -n "$JAVA_PKG" ]]; then
        packages+=("$JAVA_PKG")
    fi

    # Install packages one-by-one (don’t fail whole script on a single missing pkg)
    set +e
    for pkg in "${packages[@]}"; do
        install_pkg "$pkg"
    done
    set -e
fi

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

echo "Setup complete. Run ./run.sh to start the application."
