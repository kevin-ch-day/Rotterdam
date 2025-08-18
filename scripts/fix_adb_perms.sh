#!/usr/bin/env bash
# fix_adb_perms.sh
# Hardened fixer for ADB under an Android SDK dir (Fedora-friendly).
# - Ensures executable bits
# - Repairs SELinux labels
# - Detects noexec mounts
# - Verifies adb runs
#
# Usage:
#   ./fix_adb_perms.sh [--sdk-dir /opt/android-sdk] [--check-devices]
#
# Defaults:
#   SDK_DIR=/opt/android-sdk
#
# Notes:
#   - Will attempt to use sudo only when needed.
#   - Leaves a clear summary at the end.

set -Eeuo pipefail

# ---------- defaults / args ----------
SDK_DIR="/opt/android-sdk"
CHECK_DEVICES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sdk-dir)
      SDK_DIR="${2:-}"
      shift 2
      ;;
    --check-devices)
      CHECK_DEVICES=1
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--sdk-dir DIR] [--check-devices]"
      exit 0
      ;;
    *)
      echo "[!] Unknown arg: $1"
      exit 2
      ;;
  esac
done

PT_DIR="${SDK_DIR%/}/platform-tools"
ADB_PATH="${PT_DIR}/adb"

# ---------- pretty output ----------
OK="[OK]"; INF="[*]"; WARN="[!]"; ERR="[X]"
note(){ printf "%s %s\n" "$INF" "$*"; }
good(){ printf "%s %s\n" "$OK" "$*"; }
warn(){ printf "%s %s\n" "$WARN" "$*"; }
fail(){ printf "%s %s\n" "$ERR" "$*"; exit 1; }

# Use sudo only if not root
SUDO=""; [[ $(id -u) -ne 0 ]] && SUDO="sudo"

# ---------- prechecks ----------
note "SDK dir      : $SDK_DIR"
note "Platform-tools: $PT_DIR"
note "ADB path      : $ADB_PATH"

[[ -d "$SDK_DIR" ]] || fail "SDK dir not found: $SDK_DIR"
[[ -d "$PT_DIR" ]]  || fail "platform-tools dir not found: $PT_DIR"
[[ -e "$ADB_PATH" ]] || fail "adb not found at $ADB_PATH"

# Check mount flags (noexec will block running adb even with +x)
if command -v findmnt >/dev/null 2>&1; then
  MNT_INFO=$(findmnt -no TARGET,OPTIONS --target "$PT_DIR" 2>/dev/null || true)
  if [[ -n "$MNT_INFO" ]]; then
    MNT_OPTS=$(awk '{print $2}' <<<"$MNT_INFO" | tr -d '[]')
    if grep -qw noexec <<<"$MNT_OPTS"; then
      warn "Mount has 'noexec' set for $(awk '{print $1}' <<<"$MNT_INFO")."
      warn "You may not be able to execute adb even with +x."
      warn "Consider moving the SDK to a partition without 'noexec' (e.g., /opt)."
    fi
  fi
fi

# Show current state
note "Current adb file status:"
ls -l "$ADB_PATH" || true
if command -v file >/dev/null 2>&1; then
  file "$ADB_PATH" || true
fi
if ls -Z "$ADB_PATH" >/dev/null 2>&1; then
  note "SELinux context:"
  ls -Z "$ADB_PATH" || true
fi

# ---------- fix perms ----------
note "Ensuring adb binary is executable (755)…"
$SUDO chmod 755 "$ADB_PATH"

note "Ensuring any adb* binaries in platform-tools are executable…"
$SUDO find "$PT_DIR" -maxdepth 1 -type f -name 'adb*' -exec chmod 755 {} \;

# ---------- SELinux relabel ----------
if command -v restorecon >/dev/null 2>&1; then
  note "Restoring SELinux context labels under $SDK_DIR…"
  $SUDO restorecon -R "$SDK_DIR" || warn "restorecon reported an issue (non-fatal)."
else
  warn "restorecon not found; cannot auto-fix SELinux labels."
fi

# ---------- PATH inspection ----------
note "Checking which adb the shell would use via PATH:"
if command -v adb >/dev/null 2>&1; then
  WHICH_ADB=$(command -v adb)
  note "PATH adb: $WHICH_ADB"
else
  warn "No 'adb' found on PATH. You may want to add: export PATH=\"$PT_DIR:\$PATH\""
fi

# ---------- verification ----------
note "Attempting to run: $ADB_PATH version"
if "$ADB_PATH" version >/dev/null 2>&1; then
  good "SDK adb runs: $("$ADB_PATH" version | head -n1)"
else
  warn "Failed to run SDK adb directly. Trying PATH 'adb version'…"
  if command -v adb >/dev/null 2>&1; then
    if adb version >/dev/null 2>&1; then
      good "PATH adb runs: $(adb version | head -n1)"
    else
