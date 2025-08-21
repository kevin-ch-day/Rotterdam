# Logging

Rotterdam uses structured JSON logs written under `logs/app/`. All entry
points configure logging through `configure_logging(mode, log_to_stdout=False)`
from `utils.logging_utils.logging_config`.

## Modes

| Mode   | Log file             | Stdout default |
| ------ | ------------------- | -------------- |
| `cli`  | `logs/app/cli.log`   | disabled       |
| `server` | `logs/app/server.log` | enabled     |
| `job`  | `logs/app/jobs.log`  | disabled       |

## Re-enabling stdout logging

For CLI and background jobs, stdout logging can be enabled for debugging with
either:

```bash
python main.py --log-to-stdout
# or
ROTTERDAM_LOG_TO_STDOUT=1 python main.py
```

The server mode always logs to stdout in addition to its log file.

Logs are rotated at 1 MB with up to five backups.
