import json
import logging
from contextlib import contextmanager
import contextvars
from logging.handlers import RotatingFileHandler
from pathlib import Path


class StructuredLogger:
    """Central logging utility providing JSON logs with contextual fields."""

    _session_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
        "session_id", default=None
    )
    _device_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
        "device_serial", default=None
    )
    _action_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
        "action", default=None
    )
    _apk_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
        "apk_path", default=None
    )

    _configured: bool = False

    class _JsonFormatter(logging.Formatter):
        """Format log records as JSON including contextual metadata."""

        def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting
            log_record = {
                "time": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "module": record.name,
                "message": record.getMessage(),
            }
            session_id = StructuredLogger._session_var.get()
            device = StructuredLogger._device_var.get()
            action = StructuredLogger._action_var.get()
            apk = StructuredLogger._apk_var.get()
            if session_id:
                log_record["session_id"] = session_id
            if device:
                log_record["device_serial"] = device
            if action:
                log_record["action"] = action
            if apk:
                log_record["apk_path"] = apk
            if record.exc_info:
                log_record["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(log_record)

    @classmethod
    def _configure(cls) -> None:
        """Set up root logger with JSON formatting if not already configured."""
        if cls._configured:
            return

        # Place logs under ``<repo_root>/logs/app`` so CLI and server share output
        repo_root = Path(__file__).resolve().parents[2]
        log_dir = repo_root / "logs" / "app"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "server.log", maxBytes=1_000_000, backupCount=5
        )
        stream_handler = logging.StreamHandler()
        formatter = cls._JsonFormatter()
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(file_handler)
        root.addHandler(stream_handler)
        cls._configured = True

    @classmethod
    def get_logger(cls, name: str | None = None) -> logging.Logger:
        """Return a configured logger with JSON formatting."""
        cls._configure()
        return logging.getLogger(name)

    @classmethod
    def set_session_id(cls, session_id: str) -> None:
        """Bind a session identifier for all subsequent log records."""
        cls._session_var.set(session_id)

    @classmethod
    @contextmanager
    def context(
        cls,
        *,
        device_serial: str | None = None,
        action: str | None = None,
        apk_path: str | None = None,
    ):
        """Inject contextual fields into log records within the ``with`` block."""

        tokens: list[tuple[contextvars.ContextVar[str | None], contextvars.Token[str | None]]] = []
        if device_serial is not None:
            tokens.append((cls._device_var, cls._device_var.set(device_serial)))
        if action is not None:
            tokens.append((cls._action_var, cls._action_var.set(action)))
        if apk_path is not None:
            tokens.append((cls._apk_var, cls._apk_var.set(apk_path)))
        try:
            yield
        finally:
            for var, token in reversed(tokens):
                var.reset(token)


# Backwards compatibility helpers
def get_logger(name: str | None = None) -> logging.Logger:
    """Return a structured logger (legacy helper)."""
    return StructuredLogger.get_logger(name)


@contextmanager
def log_context(
    *,
    session_id: str | None = None,
    device_serial: str | None = None,
    action: str | None = None,
    apk_path: str | None = None,
):
    """Legacy wrapper dispatching to :class:`StructuredLogger`."""

    if session_id is not None:
        StructuredLogger.set_session_id(session_id)
    with StructuredLogger.context(
        device_serial=device_serial, action=action, apk_path=apk_path
    ):
        yield
