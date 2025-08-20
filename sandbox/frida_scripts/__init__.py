import sys
from importlib import import_module

_module = import_module('rotterdam.android.analysis.dynamic.frida')
sys.modules[__name__] = _module
__all__ = getattr(_module, "__all__", [])
