#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

usage() {
    cat <<'EOF'
Usage: ./run.sh [OPTIONS] [-- <cli args>]

Launch the Rotterdam interactive CLI. Any arguments after `--` are
passed directly to the Python CLI module.

Options:
  --setup        Run setup.sh before launching
  --setup-only   Run setup.sh and exit
  -h, --help     Show this help message
EOF
}

RUN_SETUP=0
SETUP_ONLY=0
CLI_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --setup)
            RUN_SETUP=1
            shift
            ;;
        --setup-only)
            RUN_SETUP=1
            SETUP_ONLY=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            CLI_ARGS+=("$@")
            break
            ;;
        *)
            CLI_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ $RUN_SETUP -eq 1 || ! -d .venv ]]; then
    echo "Running setup..." >&2
    if [[ ! -x ./setup.sh ]]; then
        echo "setup.sh is missing or not executable. Ensure you're in the project root." >&2
        exit 1
    fi
    ./setup.sh || {
        status=$?
        echo "setup.sh failed. You can retry with './setup.sh --skip-system' or manually install the required packages." >&2
        exit "$status"
    }
    if [[ $SETUP_ONLY -eq 1 ]]; then
        exit 0
    fi
fi

if [[ ! -f .venv/bin/activate ]]; then
    echo "Virtual environment not found. Run './setup.sh' first." >&2
    exit 1
fi

source .venv/bin/activate
exec python -m cli "${CLI_ARGS[@]}"
