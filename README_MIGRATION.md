# Migration Notes`analysis/dependencies.py` | `platform/android/analysis/static/extractors/dependencies.py` |

The project is being restructured. This batch moves a few modules and adds shims so existing imports keep working.

Symlinks used previously for cross-platform paths have been replaced with Python shims or real files so the project works on Windows and macOS.

An engine compatibility wrapper now filters unsupported SQLAlchemy keyword arguments for SQLite while preserving behaviour.

## Module map

| Old location | New location |
|--------------|--------------|
| `analysis/trust_store.json` | `data/trust_stores/android.json` |
| `orchestrator/` | `workers/` |
| `rules/android/` | `platform/android/analysis/static/rules/packs/` |
| `analysis/static.py` | `platform/android/analysis/static/pipeline.py` |
| `analysis/manifest.py` | `platform/android/analysis/static/extractors/manifest.py` |
| `analysis/permissions.py` | `platform/android/analysis/static/extractors/permissions.py` |
| `analysis/network_security.py` | `platform/android/analysis/static/extractors/network.py` |
| `analysis/secrets.py` | `platform/android/analysis/static/extractors/secrets.py` |
| `analysis/dependencies.py` | `platform/android/analysis/static/extractors/dependencies.py` |
| `analysis/cert_analysis.py` | `platform/android/analysis/static/extractors/crypto.py` |
| `analysis/signature.py` | `platform/android/analysis/static/extractors/signing.py` |
| `analysis/rules_engine.py` | `platform/android/analysis/static/rules/engine.py` |
| `analysis/report.py` | `platform/android/analysis/static/report/writer.py` |
| `analysis/androguard_utils.py` | `platform/android/analysis/static/adapters/androguard.py` |
| `analysis/yara_scan.py` | `platform/android/analysis/static/yara_scan.py` |
| `analysis/diff.py` | `platform/android/analysis/static/diff.py` |
| `risk_scoring/risk_score.py` | `platform/android/analysis/static/scoring/risk_score.py` |
| `testing/` | `tests/` |
| `devices/` | `platform/android/devices/` |
| `sandbox/` | `platform/android/analysis/dynamic/` |
| `sandbox/frida_scripts/` | `platform/android/analysis/dynamic/frida/` |
| `web/` | `ui/` |

The legacy `devices` package now proxies directly to `platform.android.devices`
instead of individual shim modules so patching utilities like `monkeypatch`
affect the real implementations.

Old import paths continue to function via Python modules and compatibility layers.
