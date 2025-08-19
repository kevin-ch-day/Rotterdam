import sys
from rotterdam.android.analysis.static.extractors import secrets as _impl

sys.modules[__name__] = _impl
