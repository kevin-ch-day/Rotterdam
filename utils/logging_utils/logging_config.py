import contextvars
import json
import logging
import os
from contextlib import contextmanager
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
    _action_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("action", default=None)
    _apk_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("apk_path", default=None)

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
    def _configure(cls, *, log_file: Path, log_to_stdout: bool) -> None:
        """Set up root logger with JSON formatting if not already configured."""
        if cls._configured:
            return

        formatter = cls._JsonFormatter()
        file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
        file_handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(file_handler)

        if log_to_stdout:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            root.addHandler(stream_handler)

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str | None = None) -> logging.Logger:
        """Return a configured logger with JSON formatting."""
        if not cls._configured:
            repo_root = Path(__file__).resolve().parents[2]
            log_dir = repo_root / "logs" / "app"
            log_dir.mkdir(parents=True, exist_ok=True)
            cls._configure(log_file=log_dir / "server.log", log_to_stdout=True)
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
    with StructuredLogger.context(device_serial=device_serial, action=action, apk_path=apk_path):
        yield


def configure_logging(mode: str, log_to_stdout: bool = False) -> None:
    """Configure structured logging for the given application mode.

    Parameters
    ----------
    mode:
        One of ``"cli"``, ``"server"`` or ``"job"`` to select the target log file.
    log_to_stdout:
        If ``True`` a stream handler is added. Regardless of this flag, setting
        the ``ROTTERDAM_LOG_TO_STDOUT`` environment variable enables stdout
        logging. The server mode always logs to stdout.
    """

    repo_root = Path(__file__).resolve().parents[2]
    log_dir = repo_root / "logs" / "app"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_map = {"cli": "cli.log", "server": "server.log", "job": "jobs.log"}
    log_file = log_dir / file_map.get(mode, "app.log")

    env_flag = os.getenv("ROTTERDAM_LOG_TO_STDOUT")
    stdout_enabled = log_to_stdout or (env_flag not in {None, "", "0", "false", "False"})
    if mode == "server":
        stdout_enabled = True

    StructuredLogger._configure(log_file=log_file, log_to_stdout=stdout_enabled)
