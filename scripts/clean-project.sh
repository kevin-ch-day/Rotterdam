#!/usr/bin/env bash
# File: scripts/clean-project.sh
# clean.sh — minimal Fedora-only cleaner for the Rotterdam repo

set -euo pipefail
OK="[OK]"; INF="[*]"; ERR="[X]"
say(){ echo "${INF} $*"; }
good(){ echo "${OK} $*"; }
fail(){ echo "${ERR} $*"; exit 1; }

usage(){ echo "Usage: $0 [--dry-run|-n]"; }

DRY_RUN=0
while (($#)); do
  case "$1" in
    -n|--dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; fail "Unknown option: $1" ;;
  esac
  shift
done

# Fedora guard
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  [[ "${ID:-}" == "fedora" || "${ID_LIKE:-}" == *"fedora"* ]] || fail "This script is restricted to Fedora."
else
  fail "Cannot detect OS (missing /etc/os-release)."
fi

# Resolve project root using git, fallback to script location
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || realpath "${SCRIPT_DIR}/..")"

cd "$PROJECT_ROOT" || fail "Cannot cd to project root: $PROJECT_ROOT"

# Repo markers
[[ -f "pyproject.toml" ]] || fail "pyproject.toml not found—are you in the repo root?"
[[ -d "server" && -d "platform/android" ]] || fail "server/ or platform/android/ missing—wrong directory?"

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
pytest_cache_count=$(count -type d -name '.pytest_cache')
mypy_cache_count=$(count -type d -name '.mypy_cache')
ruff_cache_count=$(count -type d -name '.ruff_cache')
coverage_count=$(count -type f \( -name '.coverage' -o -name '.coverage.*' -o -name 'coverage.xml' \))
egg_info_count=$(find . -maxdepth 1 -type d -name '*.egg-info' | wc -l)
build_dir=$([ -d build ] && echo 1 || echo 0)
dist_dir=$([ -d dist ] && echo 1 || echo 0)
htmlcov_dir=$([ -d htmlcov ] && echo 1 || echo 0)

say "Planned removals:"
echo "  *.pyc/pyo files:  $pyc_count"
echo "  *.log (incl. gz/xz/bz2/zip): $log_count"
echo "  __pycache__ dirs: $pycache_count"
echo "  .pytest_cache dirs: $pytest_cache_count"
echo "  .mypy_cache dirs: $mypy_cache_count"
echo "  .ruff_cache dirs: $ruff_cache_count"
echo "  coverage files: $coverage_count"
echo "  build/ dirs: $build_dir"
echo "  dist/ dirs: $dist_dir"
echo "  htmlcov/ dirs: $htmlcov_dir"
echo "  *.egg-info dirs: $egg_info_count"

# Delete files/dirs (NULL-sep for safety)
if (( pyc_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' \) -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' \) -print0 | xargs -0 -r /bin/rm -f --
  fi
fi
if (( log_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( \
      -name '*.log' -o -name '*.log.[0-9]' -o -name '*.log.[0-9].gz' -o -name '*.log.gz' -o -name '*.log.*.gz' \
      -o -name '*.log.[0-9].xz' -o -name '*.log.xz' -o -name '*.log.*.xz' \
      -o -name '*.log.[0-9].bz2' -o -name '*.log.bz2' -o -name '*.log.*.bz2' -o -name '*.log.zip' \
    \) -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( \
      -name '*.log' -o -name '*.log.[0-9]' -o -name '*.log.[0-9].gz' -o -name '*.log.gz' -o -name '*.log.*.gz' \
      -o -name '*.log.[0-9].xz' -o -name '*.log.xz' -o -name '*.log.*.xz' \
      -o -name '*.log.[0-9].bz2' -o -name '*.log.bz2' -o -name '*.log.*.bz2' -o -name '*.log.zip' \
    \) -print0 | xargs -0 -r /bin/rm -f --
  fi
fi
if (( pycache_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '__pycache__' -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '__pycache__' -print0 | xargs -0 -r /bin/rm -rf --
  fi
fi
if (( pytest_cache_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.pytest_cache' -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.pytest_cache' -print0 | xargs -0 -r /bin/rm -rf --
  fi
fi
if (( mypy_cache_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.mypy_cache' -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.mypy_cache' -print0 | xargs -0 -r /bin/rm -rf --
  fi
fi
if (( ruff_cache_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.ruff_cache' -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type d -name '.ruff_cache' -print0 | xargs -0 -r /bin/rm -rf --
  fi
fi
if (( coverage_count > 0 )); then
  if (( DRY_RUN )); then
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( -name '.coverage' -o -name '.coverage.*' -o -name 'coverage.xml' \) -print
  else
    find . \( "${PRUNE_ARGS[@]}" \) -prune -o -type f \( -name '.coverage' -o -name '.coverage.*' -o -name 'coverage.xml' \) -print0 | xargs -0 -r /bin/rm -f --
  fi
fi
if (( build_dir > 0 )); then
  if (( DRY_RUN )); then
    echo "build"
  else
    /bin/rm -rf -- build
  fi
fi
if (( dist_dir > 0 )); then
  if (( DRY_RUN )); then
    echo "dist"
  else
    /bin/rm -rf -- dist
  fi
fi
if (( htmlcov_dir > 0 )); then
  if (( DRY_RUN )); then
    echo "htmlcov"
  else
    /bin/rm -rf -- htmlcov
  fi
fi
if (( egg_info_count > 0 )); then
  if (( DRY_RUN )); then
    find . -maxdepth 1 -type d -name '*.egg-info' -print
  else
    find . -maxdepth 1 -type d -name '*.egg-info' -print0 | xargs -0 -r /bin/rm -rf --
  fi
fi

good "Cleanup complete."
