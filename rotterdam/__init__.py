"""Compatibility shim for the relocated Android modules."""
from pathlib import Path

__path__ = [str((Path(__file__).resolve().parent.parent / "platform").resolve())]
