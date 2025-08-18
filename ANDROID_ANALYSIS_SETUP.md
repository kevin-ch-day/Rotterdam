# Android Analysis Environment Setup

This guide outlines how to prepare a Fedora or Debian based system for
analyzing Android applications using both static and dynamic techniques.

## 1. System Preparation
- Install Android SDK and platform tools (`adb`, `fastboot`).
- Configure `udev` rules to allow ADB access without root. Example rule:
  `SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"`.
- Ensure your user is part of the `plugdev` (or `adbusers`) group.
- On SELinux systems, relabel analysis directories if write access is denied:
  `sudo chcon -Rt svirt_sandbox_file_t /path/to/dir`.
- Verify device connectivity with `adb devices`.

## 2. Static Analysis
- Decompile APK resources with `apktool` and sources with `jadx`.
- Inspect `AndroidManifest.xml` for excessive permissions and cleartext
  traffic (`usesCleartextTraffic="true"`).
- Search the decompiled sources for API keys or secrets.
- Check for insecure local storage such as world-readable files.
- Run the built-in Python analyzer with
  `python -m apk_analysis.apk_static <myapp.apk>` to automate the above steps
  and generate a simple report in the `analysis/` directory.
- Use the CLI to list running processes on a connected device for quick
  runtime inspection before deeper analysis.

## 3. Dynamic Analysis (Optional)
- Use a dedicated device or emulator and install monitoring tools such as
  `mitmproxy` for network inspection and `logcat` for runtime logs.
- Execute the target APK and monitor network requests, system calls, and
  background services for suspicious behaviour.
- Capture findings such as outbound connections or unexpected permission
  prompts.

## 4. Reporting
- Combine static and dynamic results into a single report.
- Prioritize issues using a scoring system (e.g., CVSS) and suggest
  mitigations.
- Store reports as JSON or CSV for further processing or integration into
  CI pipelines.

## 5. Automation and Maintenance
- Schedule updates for tools like `apktool`, `jadx`, and the Android SDK.
- Extend the `apk_analysis` Python module or add new utilities to automate
  dynamic testing and report generation.
- Integrate checks into CI to analyze new APKs continuously.

