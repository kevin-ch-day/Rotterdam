#!/usr/bin/env bash
# File: scripts/install-apktool.sh
set -euo pipefail

log(){ echo "[*] $*"; } ; good(){ echo "[OK] $*"; } ; fail(){ echo "[X] $*"; exit 1; }

# Latest stable (check https://github.com/iBotPeaches/Apktool/releases)
APKTOOL_VER="2.10.0"
BASE_URL="https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VER}"

TARGET_JAR="/usr/local/share/apktool/apktool.jar"
TARGET_BIN="/usr/local/bin/apktool"

sudo mkdir -p /usr/local/share/apktool

tmp=$(mktemp)
log "Downloading apktool ${APKTOOL_VER}..."
curl -fsSL "${BASE_URL}/apktool_${APKTOOL_VER}.jar" -o "$tmp" || fail "Download failed"
sudo mv "$tmp" "$TARGET_JAR"

log "Creating wrapper script in $TARGET_BIN"
sudo tee "$TARGET_BIN" >/dev/null <<EOF
#!/bin/sh
exec java -jar "$TARGET_JAR" "\$@"
EOF
sudo chmod +x "$TARGET_BIN"

good "apktool installed at $TARGET_BIN"
apktool --version || true
