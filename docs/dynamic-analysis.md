# Dynamic Analysis

Rotterdam's dynamic analysis simulates running an APK inside a temporary sandbox and collects runtime behavior.

## Runner

`platform/android/analysis/dynamic/runner.py` orchestrates the sandbox. It executes the target APK, loads Frida hooks, and writes logs and metrics to the specified output directory. The helper returns:

- `sandbox.log` – textual log of the session
- metrics dictionary summarizing observed behavior
- raw messages from instrumentation hooks

## Instrumentation Hooks

Hooks are JavaScript snippets located in `platform/android/analysis/dynamic/frida/` and are loaded by `instrumentation.py`. The built-in hooks include:

- `http_logger.js` – records cleartext network endpoints
- `crypto_usage.js` – notes permission usage and file writes related to cryptography

## Adding Hooks

1. Create a new `.js` file in `platform/android/analysis/dynamic/frida/` emitting messages such as `PERMISSION:`, `NETWORK:` or `FILE_WRITE:`.
2. Invoke `run_sandbox` with the hook name:
   ```python
   from platform.android.analysis.dynamic.runner import run_sandbox
   run_sandbox("app.apk", outdir, hooks=["http_logger", "my_hook"]) 
   ```
3. Metrics from emitted events will appear in `metrics.json` alongside static analysis results.

## UI Exploration

The `ui_driver.py` helper can automate basic interactions with a running app to trigger additional behavior during sandboxing.

