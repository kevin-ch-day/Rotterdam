#!/usr/bin/env bash
# diagnose-droid-emu.sh
# Fedora-focused Android Emulator/QEMU environment checker **with optional auto-fix**
# SUDO-SAFE: When run with sudo, it targets the real desktop user (SUDO_USER)
# - Default: diagnostics only (non-destructive)
# - With --fix: attempts safe remediations (packages, modules, groups, wrappers)
# - With --assume-yes: non-interactive yes to fixes
# - With --test-avd <name>: launches a safe emulator instance for smoke testing
# - With --export: writes a support bundle under ./emu-diagnose-YYYYmmdd-HHMMSS (owned by target user)

set -Eeuo pipefail
VERSION="1.4.0"

# ========================= Pretty output =========================
if [ -t 1 ]; then
  COK="[1;32m"; CWRN="[1;33m"; CERR="[1;31m"; CIN="[1;36m"; CRESET="[0m"
else
  COK=""; CWRN=""; CERR=""; CIN=""; CRESET=""
fi
OK="[OK]"; WARN="[!]"; ERR="[X]"; INF="[*]"
note(){ echo -e "${CIN}${INF}${CRESET} $*"; }
good(){ echo -e "${COK}${OK}${CRESET} $*"; }
warn(){ echo -e "${CWRN}${WARN}${CRESET} $*"; }
fail(){ echo -e "${CERR}${ERR}${CRESET} $*"; }

die(){ fail "$1"; exit "${2:-1}"; }

# ========================= Flags =========================
VERBOSE=0
TEST_AVD=""
EXPORT=0
DO_FIX=0
ASSUME_YES=0
CREATE_X11_WRAPPER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose) VERBOSE=1; shift;;
    --test-avd) TEST_AVD="${2:-}"; shift 2;;
    --export) EXPORT=1; shift;;
    --fix) DO_FIX=1; shift;;
    --assume-yes|-y) ASSUME_YES=1; shift;;
    --make-x11-wrapper) CREATE_X11_WRAPPER=1; shift;;
    -h|--help)
      cat <<EOF
Usage: $0 [--verbose] [--test-avd <AVD_NAME>] [--export] [--fix] [--assume-yes] [--make-x11-wrapper]
  --verbose          : print more details (kernel flags, env, versions)
  --test-avd <name>  : try launching the emulator with safe flags (no Vulkan, SwiftShader)
  --export           : save a support bundle with key diagnostics
  --fix              : attempt safe remediations (requires sudo for some steps)
  --assume-yes,-y    : answer yes to prompts (non-interactive)
  --make-x11-wrapper : create ~/bin/emulator-x11-safe wrapper to force X11 + SwiftShader
EOF
      exit 0;;
    *) warn "Unknown arg: $1"; shift;;
  esac
done

# ========================= SUDO-SAFE targeting =========================
# Determine the intended desktop user & home even when running with sudo
TARGET_USER="${SUDO_USER:-$(id -un)}"
if ! getent passwd "$TARGET_USER" >/dev/null; then die "Cannot resolve target user ($TARGET_USER)"; fi
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
TARGET_SHELL="$(getent passwd "$TARGET_USER" | cut -d: -f7)"

# Run a command as the target user with a login-like environment
run_as_target(){ sudo -u "$TARGET_USER" -H env HOME="$TARGET_HOME" bash -lc "$*"; }

# Same but keep root when not using sudo
run_root_or_self(){ bash -lc "$*"; }

# Wrapper to use sudo for privileged ops only when needed
run_sudo(){ if [[ $EUID -eq 0 ]]; then bash -lc "$*"; else sudo bash -lc "$*"; fi }

# Prompt helper
confirm(){ [[ $ASSUME_YES -eq 1 ]] && return 0; read -rp "Proceed? [y/N] " ans; [[ "${ans:-}" =~ ^[Yy]$ ]]; }

val_or_unknown(){ [[ -n "${1:-}" ]] && echo "$1" || echo "unknown"; }

# ========================= 1) System & session =========================
SECTION(){ echo; echo "===================================================================="; echo "[$(date +'%Y-%m-%d %I:%M:%S %p')] $*"; echo "===================================================================="; }

SECTION "System & session"
OS="$(grep '^NAME=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"')"
VER="$(grep '^VERSION=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"')"
KERNEL="$(uname -r)"
# Try to detect the target user's active session type even under sudo/tty
SESSION_TYPE="${XDG_SESSION_TYPE:-}"
if [[ -z "$SESSION_TYPE" ]]; then
  SESSION_TYPE=$(loginctl list-sessions 2>/dev/null | awk -v u="$TARGET_USER" '$0 ~ u {print $2}' | xargs -r -I{} loginctl show-session {} -p Type 2>/dev/null | cut -d= -f2 | head -n1)
  [[ -z "$SESSION_TYPE" ]] && SESSION_TYPE="tty"
fi
DESKTOP="${XDG_CURRENT_DESKTOP:-unknown}"
GPU="$(lspci | grep -E 'VGA|3D' || true)"

note "Running as: $(id -un)  |  Target user: $TARGET_USER  |  Home: $TARGET_HOME"
note "OS            : ${OS:-unknown} ${VER:-}"
note "Kernel        : $KERNEL"
note "Session       : ${SESSION_TYPE:-unknown}  (Wayland=wayland, X11=x11)"
note "Desktop       : $DESKTOP"
note "GPU           : $(val_or_unknown "$GPU")"

if [[ "$SESSION_TYPE" == "wayland" ]]; then
  warn "Wayland session detected for $TARGET_USER. The emulator may be more stable via X11 toolkit."
fi

# ========================= 2) CPU virtualization & KVM =========================
SECTION "CPU virtualization & KVM access"
CPUFLAGS="$(grep -m1 -E 'flags|Features' /proc/cpuinfo || true)"
if echo "$CPUFLAGS" | grep -qw vmx; then good "Intel VMX supported."; elif echo "$CPUFLAGS" | grep -qw svm; then good "AMD SVM supported."; else fail "No hardware virtualization flags (vmx/svm) seen. Enable SVM/VT-x in BIOS/UEFI."; fi

if lsmod | grep -q '^kvm\b'; then
  good "kvm module loaded."
else
  warn "kvm module not loaded."
  if [[ $DO_FIX -eq 1 ]]; then
    note "Attempting to load kvm module(s)..."
    if confirm; then
      run_sudo "modprobe kvm || true"
      run_sudo "modprobe kvm_intel 2>/dev/null || modprobe kvm_amd 2>/dev/null || true"
    else warn "Skipped loading kvm modules"; fi
  fi
fi

if [[ -e /dev/kvm ]]; then
  good "/dev/kvm present."
else
  warn "/dev/kvm missing."
  if [[ $DO_FIX -eq 1 ]]; then
    note "Installing virtualization packages (qemu-kvm, libvirt, virt-install) may create /dev/kvm."
    if confirm; then
      run_sudo "dnf install -y @virtualization qemu-kvm libvirt virt-install || true"
      run_sudo "systemctl enable --now libvirtd || true"
    else warn "Skipped virtualization packages"; fi
  fi
fi

# Show & fix perms against the *target* user's access
note "Permissions for /dev/kvm (if present):"
(getfacl -p /dev/kvm 2>/dev/null || ls -l /dev/kvm) | sed 's/^/    /' || true
if id -nG "$TARGET_USER" | grep -qw kvm; then
  good "Target user $TARGET_USER is in 'kvm' group."
else
  warn "Target user $TARGET_USER is NOT in 'kvm' group."
  if [[ $DO_FIX -eq 1 ]]; then
    note "Adding $TARGET_USER to kvm group (will require re-login)."
    if confirm; then run_sudo "usermod -aG kvm $TARGET_USER"; good "Added to kvm group. Log out/in or 'newgrp kvm'."; else warn "Skipped adding to kvm group"; fi
  fi
fi

# Optional hardening: if /dev/kvm is world-writable (0666), tighten to 0660 via udev rule
if [[ -e /dev/kvm ]]; then
  CURMODE="$(stat -c '%a' /dev/kvm 2>/dev/null || echo '-')"
  CURGRP="$(stat -c '%G' /dev/kvm 2>/dev/null || echo '-')"
  if [[ "$CURMODE" == "666" || "$CURGRP" != "kvm" ]]; then
    warn "/dev/kvm mode/group is ${CURMODE}:${CURGRP}. Recommended is 0660:kvm."
    if [[ $DO_FIX -eq 1 ]]; then
      note "Create udev rule to enforce MODE=0660, GROUP=kvm? (/etc/udev/rules.d/65-kvm.rules)"
      if confirm; then
        run_sudo "bash -lc 'echo SUBSYSTEM==\"misc\", KERNEL==\"kvm\", GROUP=\"kvm\", MODE=\"0660\" > /etc/udev/rules.d/65-kvm.rules'"
        run_sudo "udevadm control --reload && udevadm trigger /dev/kvm || true"
        good "Applied udev rule for /dev/kvm."
      else warn "Skipped udev rule"; fi
    fi
  fi
fi

# ========================= 3) Graphics/Vulkan runtime checks =========================
SECTION "Graphics/Vulkan runtime checks"
MESA_PACKAGES=(mesa-demos)
VULKAN_PACKAGES=(vulkan-tools)
if run_root_or_self "command -v glxinfo" >/dev/null 2>&1; then
  GL_RENDERER="$(glxinfo -B 2>/dev/null | awk -F: '/OpenGL renderer string/ {print $2}' | sed 's/^ //')"
  note "OpenGL renderer: ${GL_RENDERER:-unknown}"
else
  warn "glxinfo not found (mesa-demos)."
  if [[ $DO_FIX -eq 1 ]]; then
    note "Install mesa-demos?"
    if confirm; then run_sudo "dnf install -y ${MESA_PACKAGES[*]}"; else warn "Skipped mesa-demos"; fi
  fi
fi

if run_root_or_self "command -v vulkaninfo" >/dev/null 2>&1; then
  if vulkaninfo >/dev/null 2>&1; then good "vulkaninfo ran successfully."; else warn "vulkaninfo exists but failed; Vulkan stack may be broken. Consider disabling Vulkan for emulator."; fi
else
  warn "vulkaninfo not found (vulkan-tools)."
  if [[ $DO_FIX -eq 1 ]]; then
    note "Install vulkan-tools?"
    if confirm; then run_sudo "dnf install -y ${VULKAN_PACKAGES[*]}"; else warn "Skipped vulkan-tools"; fi
  fi
fi

# ========================= 4) Flatpak vs tarball =========================
SECTION "Android Studio / Emulator origin"
FLATPAK_STUDIO=""
if run_root_or_self "command -v flatpak" >/dev/null 2>&1; then FLATPAK_STUDIO="$(run_as_target "flatpak list --app" 2>/dev/null | grep -i 'Android Studio' || true)"; fi
if [[ -n "$FLATPAK_STUDIO" ]]; then
  warn "Android Studio installed via Flatpak for $TARGET_USER:"; echo "$FLATPAK_STUDIO" | sed 's/^/    /'
  warn "Flatpak sandbox can cause GL/Vulkan mismatches for the emulator."
else
  good "No Android Studio Flatpak detected (or flatpak not installed)."
fi

# ========================= 5) Locate SDK / emulator =========================
SECTION "Android SDK / Emulator discovery"
SDK_DIRS=()
[[ -n "${ANDROID_SDK_ROOT:-}" ]] && SDK_DIRS+=("$ANDROID_SDK_ROOT")
[[ -n "${ANDROID_HOME:-}" ]] && SDK_DIRS+=("$ANDROID_HOME")
SDK_DIRS+=("$TARGET_HOME/Android/Sdk" "$TARGET_HOME/android-sdk" "/opt/android-sdk" "/opt/android-sdk-linux")

EMU_BIN="$(run_as_target "command -v emulator" || true)"
if [[ -z "$EMU_BIN" ]]; then
  for d in "${SDK_DIRS[@]}"; do
    [[ -x "$d/emulator/emulator" ]] && EMU_BIN="$d/emulator/emulator" && break
  done
fi

if [[ -n "$EMU_BIN" ]]; then
  good "Found emulator: $EMU_BIN"
  if run_as_target "$EMU_BIN -version" >/tmp/emu_ver.$$ 2>&1; then note "Emulator version:"; sed 's/^/    /' /tmp/emu_ver.$$; else warn "Failed to run '$EMU_BIN -version' as $TARGET_USER"; fi
else
  warn "Android emulator not found for $TARGET_USER."
  if [[ $DO_FIX -eq 1 ]]; then
    if run_as_target "command -v sdkmanager" >/dev/null 2>&1; then
      note "Install the Emulator via sdkmanager for $TARGET_USER?"
      if confirm; then run_as_target "sdkmanager --install 'emulator'" || true; else warn "Skipped sdkmanager install"; fi
    else
      warn "sdkmanager not found. Install Android commandline-tools first for $TARGET_USER."
    fi
  fi
fi

# ADB presence
if run_as_target "command -v adb" >/dev/null 2>&1; then
  good "adb present for $TARGET_USER: $(run_as_target 'command -v adb')"; run_as_target "adb --version" | sed 's/^/    /'
else
  warn "adb not found in PATH for $TARGET_USER."
fi

# AVDs
AVD_ROOT="$TARGET_HOME/.android/avd"
if [[ -d "$AVD_ROOT" ]]; then
  note "Discovered AVDs in $AVD_ROOT:"; find "$AVD_ROOT" -maxdepth 1 -name "*.avd" -printf "    %f\n" | sed 's/\.avd$//' || true
else
  warn "No AVD directory found at $AVD_ROOT (create an AVD in AVD Manager)."
fi

# ========================= 6) Recent crashes via coredumpctl =========================
SECTION "Recent emulator/QEMU crashes (systemd-coredump)"
if run_root_or_self "command -v coredumpctl" >/dev/null 2>&1; then
  if coredumpctl list qemu-system-x86_64 | grep -q qemu-system-x86_64; then
    note "Last crash summary (qemu-system-x86_64):"; coredumpctl info qemu-system-x86_64 | sed -n '1,40p' | sed 's/^/    /'
  else
    good "No recent qemu-system-x86_64 coredumps found."
  fi
else
  warn "coredumpctl not available."
fi

# ========================= 7) Create X11 + SwiftShader wrapper =========================
if [[ $CREATE_X11_WRAPPER -eq 1 ]]; then
  SECTION "Creating emulator X11/SwiftShader wrapper for $TARGET_USER"
  WRAP_DIR="$TARGET_HOME/bin"; run_sudo "mkdir -p '$WRAP_DIR' && chown $TARGET_USER:$TARGET_USER '$WRAP_DIR'"
  WRAP_PATH="$WRAP_DIR/emulator-x11-safe"
  run_sudo "bash -lc 'cat > "$WRAP_PATH" <<\'WRAP'" && cat <<'WRAP' | sudo tee "$WRAP_PATH" >/dev/null
#!/usr/bin/env bash
set -euo pipefail
export QT_QPA_PLATFORM=xcb
exec emulator -gpu swiftshader_indirect -feature -Vulkan "$@"
WRAP
  run_sudo "chmod +x '$WRAP_PATH' && chown $TARGET_USER:$TARGET_USER '$WRAP_PATH'"
  good "Created $WRAP_PATH"
  if ! run_as_target "echo \"$PATH\"" | grep -q "$TARGET_HOME/bin"; then warn "Consider adding ~/bin to PATH for $TARGET_USER (echo 'export PATH=\"$HOME/bin:$PATH\"' >> $TARGET_HOME/.bashrc)"; fi
fi

# ========================= 8) Recommendations =========================
SECTION "Recommendations"
echo "  • If crashes persist on Wayland, launch with X11 toolkit:"
echo "      QT_QPA_PLATFORM=xcb ${EMU_BIN:-emulator} -avd <AVD> -gpu swiftshader_indirect -feature -Vulkan"
echo "  • Prefer Software/SwiftShader GPU in AVD settings (equiv to -gpu swiftshader_indirect)."
echo "  • Disable Vulkan with '-feature -Vulkan'; use OpenGL ES via SwiftShader."
echo "  • Ensure $TARGET_USER is in the 'kvm' group, then re-login:  sudo usermod -aG kvm $TARGET_USER"
echo "  • Avoid Flatpak Studio for emulator work if you hit GL/Vulkan issues; use Google's tarball."
echo "  • Keep Mesa and kernel updated:  sudo dnf upgrade --refresh"

# ========================= 9) Optional: test launch =========================
if [[ -n "$TEST_AVD" && -n "${EMU_BIN:-}" ]]; then
  SECTION "Test-launching AVD '${TEST_AVD}' with safe flags as $TARGET_USER"
  set +e
  run_as_target "\"$EMU_BIN\" -avd '$TEST_AVD' -gpu swiftshader_indirect -feature -Vulkan -no-snapshot -accel on -verbose & echo $!" >/tmp/emu_pid.$$ 2>/dev/null
  EMU_PID=$(cat /tmp/emu_pid.$$ 2>/dev/null || echo 0)
  sleep 8
  if [[ $EMU_PID -gt 0 ]] && ps -p "$EMU_PID" >/dev/null 2>&1; then
    good "Emulator started without immediate crash (PID $EMU_PID)."
    note "Closing test instance..."; run_root_or_self "kill $EMU_PID" 2>/dev/null || true
  else
    fail "Emulator process exited quickly; check the console above for clues."
  fi
  set -e
fi

# ========================= 10) Export bundle =========================
if [[ $EXPORT -eq 1 ]]; then
  SECTION "Exporting support bundle"
  SAVE_DIR="emu-diagnose-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$SAVE_DIR"
  {
    echo "diagnose-droid-emu.sh v$VERSION";
    echo "Run at: $(date +'%Y-%m-%d %I:%M:%S %p')";
    echo "Runner: $(id -un)  |  Target: $TARGET_USER";
    echo "OS: ${OS:-} ${VER:-}";
    echo "Kernel: $KERNEL";
    echo "Session: ${SESSION_TYPE:-unknown}";
    echo "Desktop: ${DESKTOP:-unknown}";
    echo "GPU: $(val_or_unknown "$GPU")";
  } > "$SAVE_DIR/summary.txt"
  run_root_or_self "lsmod" > "$SAVE_DIR/lsmod.txt" 2>/dev/null || true
  id -nG "$TARGET_USER" > "$SAVE_DIR/target-groups.txt" 2>/dev/null || true
  env > "$SAVE_DIR/env-runner.txt" 2>/dev/null || true
  [[ -n "${EMU_BIN:-}" ]] && run_as_target "\"$EMU_BIN\" -version" > "$SAVE_DIR/emulator-version.txt" 2>/dev/null || true
  run_as_target "adb --version" > "$SAVE_DIR/adb-version.txt" 2>/dev/null || true
  (coredumpctl info qemu-system-x86_64 || true) > "$SAVE_DIR/coredumpctl-qemu.txt" 2>/dev/null || true
  glxinfo -B > "$SAVE_DIR/glxinfo.txt" 2>/dev/null || true
  vulkaninfo > "$SAVE_DIR/vulkaninfo.txt" 2>/dev/null || true
  run_as_target "flatpak list --app" > "$SAVE_DIR/flatpak-list.txt" 2>/dev/null || true
  # hand ownership back to the target user if running as root
  if [[ $EUID -eq 0 ]]; then chown -R "$TARGET_USER:$TARGET_USER" "$SAVE_DIR" || true; fi
  good "Support bundle created at: $SAVE_DIR/ (owned by $TARGET_USER)"
fi

# ========================= 11) Verbose tail =========================
if [[ $VERBOSE -eq 1 ]]; then
  SECTION "Verbose details"
  echo "[/proc/cpuinfo flags line]"; echo "$CPUFLAGS" | sed 's/^/    /'
  echo; echo "[Relevant env vars for $TARGET_USER]"; run_as_target "env | grep -E 'ANDROID_|JAVA_HOME|QT_QPA_PLATFORM|MESA_|LIBGL'" | sed 's/^/    /' || true
fi

echo; good "Done. Fix mode: $([[ $DO_FIX -eq 1 ]] && echo ON || echo OFF). Target user: $TARGET_USER"