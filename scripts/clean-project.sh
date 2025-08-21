#!/usr/bin/env bash
# File: scripts/clean-project.sh
# clean.sh — minimal Fedora-only cleaner for the Rotterdam repo

set -euo pipefail
OK="[OK]"; INF="[*]"; ERR="[X]"
say(){ echo "${INF} $*"; }
good(){ echo "${OK} $*"; }
fail(){ echo "${ERR} $*"; exit 1; }

# Fedora guard
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  [[ "${ID:-}" == "fedora" || "${ID_LIKE:-}" == *"fedora"* ]] || fail "This script is restricted to Fedora."
else
  fail "Cannot detect OS (missing /etc/os-release)."
fi

# Enforce exact project root
EXPECTED_ROOT="/home/linuxadmin/Downloads/Rotterdam"
PROJECT_ROOT="$(realpath ".")"
[[ "$PROJECT_ROOT" == "$EXPECTED_ROOT" ]] || fail "Run this from $EXPECTED_ROOT (you are in $PROJECT_ROOT)."

# Repo markers
[[ -f "pyproject.toml" ]] || fail "pyproject.toml not found—are you in the repo root?"
[[ -d "server" && -d "platform/android" ]] || fail "server/ or platform/android/ missing—wrong directory?"

cd "$PROJECT_ROOT"
say "Cleaning repo at: $PROJECT_ROOT"

# Don’t traverse heavy dirs
PRUNE_ARGS=( -path './.git' -o -path './.venv' -o -path './node_modules' -o -path './dist' -o -path './build' )

# Count helper (with prune)
count() { find . \( "${PRUNE_ARGS[@]}" \) -prune -o "$@" -print 2>/dev/null | wc -l; }

# Targets
pyc_count=$(count -type f \( -name '*.pyc' -o -name '*.pyo' \))
log_count=$(count -type f \( \
  -name '*.log' -o -name '*.log.[0-9]' -o -name '*.log.[0-9].gz' -o -name '*.log.gz' -o -name '*.log.*.gz' \
  -o -name '*.log.[0-9].xz' -o -name '*.log.xz' -o -name '*.log.*.xz' \
  -o -name '*.log.[0-9].bz2' -o -name '*.log.bz2' -o -name '*.log.*.bz2' -o -name '*.log.zip' \
\))
pycache_count=$(count -type d -name '__pycache__')

say "Planned removals:"
echo "  *.pyc/pyo files:  $pyc_count"
echo "  *.log (incl. gz/xz/bz2/zip): $log_count"
echo "  __pycache__ dirs: $pycache_count"

# Delete files/dirs (NULL-sep for safety)
if (( pyc_count > 0 )); then
  find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' \) -print0 \
    | xargs -0 -r /bin/rm -f --
fi
if (( log_count > 0 )); then
  find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( \
    -name '*.log' -o -name '*.log.[0-9]' -o -name '*.log.[0-9].gz' -o -name '*.log.gz' -o -name '*.log.*.gz' \
    -o -name '*.log.[0-9].xz' -o -name '*.log.xz' -o -name '*.log.*.xz' \
    -o -name '*.log.[0-9].bz2' -o -name '*.log.bz2' -o -name '*.log.*.bz2' -o -name '*.log.zip' \
  \) -print0 | xargs -0 -r /bin/rm -f --
fi
if (( pycache_count > 0 )); then
  find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '__pycache__' -print0 \
    | xargs -0 -r /bin/rm -rf --
fi

good "Cleanup complete."
