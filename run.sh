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
  --setup [ARGS]        Run setup.sh before launching; any following arguments
                        (before `--`) are forwarded to setup.sh
  --setup-only [ARGS]   Run setup.sh with arguments and exit without launching
                        the CLI
  -h, --help            Show this help message

Examples:
  ./run.sh --setup --skip-system   # run setup skipping system packages
  ./run.sh --setup-only --skip-system  # run setup and exit
EOF
}

RUN_SETUP=0
RUN_SETUP_ONLY=0
SETUP_ARGS=()
CLI_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --setup)
            RUN_SETUP=1
            shift
            ;;
        --setup-only)
            RUN_SETUP=1
            RUN_SETUP_ONLY=1
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
            if [[ $RUN_SETUP -eq 1 ]]; then
                SETUP_ARGS+=("$1")
            else
                CLI_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

if [[ $RUN_SETUP -eq 1 || ! -d .venv ]]; then
    echo "Running setup..." >&2
    ./setup.sh "${SETUP_ARGS[@]}"
    if [[ $RUN_SETUP_ONLY -eq 1 ]]; then
        exit 0
    fi
fi

source .venv/bin/activate
exec python -m cli "${CLI_ARGS[@]}"
