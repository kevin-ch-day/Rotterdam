import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


# Provide a minimal ``rotterdam`` namespace for modules expecting it.
if "rotterdam" not in sys.modules:
    rotterdam = types.ModuleType("rotterdam")
    rotterdam.__path__ = [str(ROOT)]
    sys.modules["rotterdam"] = rotterdam

    android_pkg = types.ModuleType("rotterdam.android")
    android_pkg.__path__ = [str(ROOT / "platform" / "android")]
    sys.modules["rotterdam.android"] = android_pkg

    devices_pkg = types.ModuleType("rotterdam.android.devices")
    devices_pkg.__path__ = [str(ROOT / "platform" / "android" / "devices")]
    sys.modules["rotterdam.android.devices"] = devices_pkg
    _load("rotterdam.android.devices.discovery", "platform/android/devices/discovery.py")
    _load("rotterdam.android.devices.props", "platform/android/devices/props.py")
    _load("rotterdam.android.devices.adb", "platform/android/devices/adb.py")

    analysis_pkg = types.ModuleType("rotterdam.android.analysis")
    analysis_pkg.__path__ = [str(ROOT / "platform" / "android" / "analysis")]
    sys.modules["rotterdam.android.analysis"] = analysis_pkg

    static_pkg = types.ModuleType("rotterdam.android.analysis.static")
    static_pkg.__path__ = [str(ROOT / "platform" / "android" / "analysis" / "static")]
    sys.modules["rotterdam.android.analysis.static"] = static_pkg

    extractors_pkg = types.ModuleType("rotterdam.android.analysis.static.extractors")
    extractors_pkg.__path__ = [
        str(ROOT / "platform" / "android" / "analysis" / "static" / "extractors")
    ]
    sys.modules["rotterdam.android.analysis.static.extractors"] = extractors_pkg
    _load(
        "rotterdam.android.analysis.static.extractors.manifest",
        "platform/android/analysis/static/extractors/manifest.py",
    )

# Stub out optional dependency used by job_service
if "risk_scoring" not in sys.modules:
    risk_scoring = types.ModuleType("risk_scoring")
    risk_scoring.risk_score = types.ModuleType("risk_scoring.risk_score")

    def calculate_risk_score(static, dynamic):  # type: ignore[unused-argument]
        return 0.0

    risk_scoring.risk_score.calculate_risk_score = calculate_risk_score
    sys.modules["risk_scoring"] = risk_scoring
    sys.modules["risk_scoring.risk_score"] = risk_scoring.risk_score
