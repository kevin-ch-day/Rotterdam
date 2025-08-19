import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextlib import contextmanager
import contextvars

# Context variables for device and app metadata
_device_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("device", default=None)
_app_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("app", default=None)


class JsonFormatter(logging.Formatter):
    """Format log records as JSON including context metadata."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        device = _device_var.get()
        app = _app_var.get()
        if device:
            log_record["device"] = device
        if app:
            log_record["app"] = app
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def _build_handler() -> logging.Handler:
    """Create a rotating file handler writing to reports/logs/audit.log."""
    log_dir = Path(__file__).resolve().parent / "reports" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "audit.log", maxBytes=1_000_000, backupCount=5
    )
    stream_handler = logging.StreamHandler()

    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
    return root


_root_logger: logging.Logger = _build_handler()


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger with JSON formatting."""
    return logging.getLogger(name)


@contextmanager
def log_context(*, device: str | None = None, app: str | None = None):
    """Context manager to inject device/app metadata into log records."""
    token_dev = _device_var.set(device) if device is not None else None
    token_app = _app_var.set(app) if app is not None else None
    try:
        yield
    finally:
        if token_dev is not None:
            _device_var.reset(token_dev)
        if token_app is not None:
            _app_var.reset(token_app)
