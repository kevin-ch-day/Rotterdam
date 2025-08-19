"""Create database tables on the configured engine."""

from .repository import get_engine
from .models import Base


def init_db() -> None:
    """Create all tables on the configured engine."""
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    print("[OK] Tables created (or already exist).")


def main() -> None:  # pragma: no cover - thin wrapper for CLI usage
    init_db()


if __name__ == "__main__":  # pragma: no cover
    main()
