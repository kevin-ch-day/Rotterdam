# Environment Configuration

Rotterdam reads configuration from environment variables using the
[`pydantic-settings`](https://pydantic-docs.helpmanual.io/latest/usage/pydantic_settings/)
package. Defaults are defined in `settings/app.py` and used throughout
the project.

| Variable            | Default     | Description                                       |
|---------------------|-------------|---------------------------------------------------|
| `ROTTERDAM_APP_HOST`| `127.0.0.1` | Host interface for the web server                 |
| `ROTTERDAM_APP_PORT`| `8765`      | Port for the web server                           |
| `UVICORN_LOG_LEVEL` | `info`      | Log level for Uvicorn                             |
| `OPEN_BROWSER`      | `true`      | Whether to open a browser when server starts      |

These settings are accessed via `settings.get_settings()`.
