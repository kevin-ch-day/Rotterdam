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
  --setup       Run setup.sh before launching
  -h, --help    Show this help message
EOF
}

RUN_SETUP=0
CLI_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --setup)
            RUN_SETUP=1
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
    ./setup.sh
fi

source .venv/bin/activate
exec python -m cli "${CLI_ARGS[@]}"
