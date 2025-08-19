import sys
from importlib import import_module

_module = import_module('rotterdam.android.apps')
sys.modules[__name__] = _module
