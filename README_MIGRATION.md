# Migration Notes

The project is being restructured. This batch moves a few modules and adds shims so existing imports keep working.

Symlinks used previously for cross-platform paths have been replaced with Python shims or real files so the project works on Windows and macOS.

An engine compatibility wrapper now filters unsupported SQLAlchemy keyword arguments for SQLite while preserving behaviour.

## Module map

| Old location | New location |
|--------------|--------------|
| `analysis/trust_store.json` | `data/trust_stores/android.json` |
| `orchestrator/` | `workers/` |
| `rules/android/` | `platform/android/analysis/static/rules/packs/` |
| `analysis/static.py` | `rotterdam/android/analysis/static/pipeline.py` |
| `analysis/manifest.py` | `rotterdam/android/analysis/static/extractors/manifest.py` |
| `analysis/permissions.py` | `rotterdam/android/analysis/static/extractors/permissions.py` |
| `analysis/network_security.py` | `rotterdam/android/analysis/static/extractors/network.py` |
| `analysis/secrets.py` | `rotterdam/android/analysis/static/extractors/secrets.py` |
| `analysis/cert_analysis.py` | `rotterdam/android/analysis/static/extractors/crypto.py` |
| `analysis/signature.py` | `rotterdam/android/analysis/static/extractors/signing.py` |
| `analysis/rules_engine.py` | `rotterdam/android/analysis/static/rules/engine.py` |
| `analysis/report.py` | `rotterdam/android/analysis/static/report/writer.py` |
| `analysis/androguard_utils.py` | `rotterdam/android/analysis/static/adapters/androguard.py` |
| `analysis/yara_scan.py` | `rotterdam/android/analysis/static/yara_scan.py` |
| `analysis/diff.py` | `rotterdam/android/analysis/static/diff.py` |
| `testing/` | `tests/` |
| `devices/` | `rotterdam/android/devices/` |
| `sandbox/` | `rotterdam/android/analysis/dynamic/` |

The legacy `devices` package now proxies directly to `rotterdam.android.devices`
instead of individual shim modules so patching utilities like `monkeypatch`
affect the real implementations.

Old import paths continue to function via Python modules and compatibility layers.
