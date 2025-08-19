from pathlib import Path

PACKS_DIR = (
    Path(__file__).resolve().parents[2]
    / "rotterdam"
    / "android"
    / "analysis"
    / "static"
    / "rules"
    / "packs"
)

__all__ = ["PACKS_DIR"]
