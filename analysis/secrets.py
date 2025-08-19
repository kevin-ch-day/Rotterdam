import sys
from importlib import import_module

_module = import_module("rotterdam.android.analysis.static.extractors.secrets")
sys.modules[__name__] = _module
