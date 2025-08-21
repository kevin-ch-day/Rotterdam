#!/usr/bin/env bash
# File: scripts/install-aapt2.sh
# install-aapt2.sh — Fedora-only one-shot installer for aapt2 via Android SDK build-tools

set -euo pipefail
OK="[OK]"; WRN="[!]"; ERR="[X]"; INF="[*]"
log(){ echo "${INF} $*"; } ; good(){ echo "${OK} $*"; } ; warn(){ echo "${WRN} $*"; } ; fail(){ echo "${ERR} $*"; exit 1; }

# Fedora guard
if [[ -r /etc/os-release ]]; then . /etc/os-release
  [[ "${ID:-}" == "fedora" || "${ID_LIKE:-}" == *"fedora"* ]] || fail "This script targets Fedora."
else fail "Cannot detect OS."; fi

# Invoking user + SDK root (works even with sudo)
INVOKING_USER="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$INVOKING_USER" | cut -d: -f6 || echo "/home/$INVOKING_USER")"
SDK_ROOT="${USER_HOME}/Android/Sdk"
CMDLINE_LATEST="$SDK_ROOT/cmdline-tools/latest"
SDKM="$CMDLINE_LATEST/bin/sdkmanager"

have(){ command -v "$1" >/dev/null 2>&1; }
as_root(){ command -v sudo >/dev/null || fail "sudo required"; sudo -n true 2>/dev/null || log "sudo may prompt…"; sudo "$@"; }
fetch(){ local u="$1" o="$2"; if have curl; then curl -fsSL "$u" -o "$o"; elif have wget; then wget -qO "$o" "$u"; else fail "Need curl/wget"; fi; }
own_fix(){ [[ -n "${SUDO_USER:-}" ]] && as_root chown -R "$INVOKING_USER:$INVOKING_USER" "$SDK_ROOT" || true; }

# 1) OS deps
log "Installing system dependencies (curl/wget, unzip, platform tools, Java)…"
as_root dnf install -y curl wget unzip android'-'tools || true
as_root dnf install -y java-21-openjdk-headless || as_root dnf install -y java-17-openjdk-headless || true

# 2) Fast-path if aapt2 already works
if have aapt2; then
  good "aapt2 already available: $(command -v aapt2)"
  aapt2 version || true
  exit 0
fi

# 3) Ensure cmdline-tools (sdkmanager)
mkdir -p "$SDK_ROOT"
if [[ ! -x "$SDKM" ]]; then
  log "Installing Android command-line tools → $CMDLINE_LATEST"
  tmpz="$(mktemp)"; tmpd="$(mktemp -d)"
  fetch "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" "$tmpz"
  mkdir -p "$SDK_ROOT/cmdline-tools"
  unzip -q "$tmpz" -d "$tmpd"; rm -f "$tmpz"
  [[ -d "$tmpd/cmdline-tools" ]] || { rm -rf "$tmpd"; fail "Unexpected zip layout"; }
  rm -rf "$CMDLINE_LATEST"; mkdir -p "$CMDLINE_LATEST"
  mv "$tmpd"/cmdline-tools/* "$CMDLINE_LATEST"/ 2>/dev/null || true
  [[ -x "$SDKM" ]] || { mv "$CMDLINE_LATEST"/cmdline-tools/* "$CMDLINE_LATEST"/ 2>/dev/null || true; rmdir "$CMDLINE_LATEST/cmdline-tools" 2>/dev/null || true; }
  rm -rf "$tmpd"
  chmod +x "$CMDLINE_LATEST"/bin/* 2>/dev/null || true
  own_fix
fi

# 4) Accept licenses + platform-tools
export ANDROID_SDK_ROOT="$SDK_ROOT"; export ANDROID_HOME="$SDK_ROOT"; export PATH="$CMDLINE_LATEST/bin:$PATH"
have sdkmanager || fail "sdkmanager missing after install"
yes | sdkmanager --licenses >/dev/null || true
yes | sdkmanager "platform-tools" >/dev/null || true

# 5) Build-tools (auto, fallback 35→34)
choose_build_tools() {
  local want=""
  if sdkmanager --list | grep -q 'build-tools;'; then
    want="$(sdkmanager --list | sed -n 's/.*build-tools;\([0-9.]\+\).*/\1/p' | sort -V | tail -n1 || true)"
  fi
  [[ -n "$want" ]] || want="35.0.0"
  if ! yes | sdkmanager "build-tools;$want" >/dev/null 2>&1; then
    warn "Failed to install $want — trying 34.0.0"
    want="34.0.0"
    yes | sdkmanager "build-tools;$want" >/dev/null 2>&1 || fail "Unable to install Android build-tools."
  fi
  echo "$want"
}

log "Installing Android build-tools (for aapt2)…"
BT_VER="$(choose_build_tools)"; own_fix
AAPT2_BIN="$SDK_ROOT/build-tools/$BT_VER/aapt2"
[[ -x "$AAPT2_BIN" ]] || fail "aapt2 missing after install: $AAPT2_BIN"

# 6) Normalize symlink to /usr/local/bin (consistent for user & sudo)
log "Linking /usr/local/bin/aapt2 -> $AAPT2_BIN"
as_root ln -sf "$AAPT2_BIN" /usr/local/bin/aapt2
# Remove any stray /usr/local/sbin/aapt2 to avoid confusion
as_root rm -f /usr/local/sbin/aapt2 2>/dev/null || true

# 7) Final report
good "aapt2 installed at: $AAPT2_BIN"
which aapt2 || true; aapt2 version || true
cat <<'EOF'

Tip: add sdkmanager/adb to PATH (optional):
  echo 'export ANDROID_SDK_ROOT="$HOME/Android/Sdk"' >> ~/.bashrc
  echo 'export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"' >> ~/.bashrc

EOF
