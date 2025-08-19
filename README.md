# Rotterdam

Rotterdam is a toolkit for analyzing Android applications and devices. It provides utilities for extracting and scanning APKs, evaluating device behavior, and reporting findings.

## Development

Set up a Python environment and install the project's dependencies.
Dependencies are listed in `requirements.txt`, including the MySQL driver
`mysql-connector-python` and YARA bindings via `yara-python`.
The YARA wrapper requires the system `libyara` library; on Debian-based
systems it can be installed with `apt-get install libyara-dev`.

### Database configuration

The repository uses SQLAlchemy for persistence. By default an in-memory
SQLite database is used, but MySQL is also supported. Configure the database
connection in one of two ways:

1. Provide a full SQLAlchemy URL via ``DATABASE_URL``::

   ``export DATABASE_URL="mysql+mysqlconnector://user:pass@host/db"``

2. Set individual MySQL parameters and they will be assembled into a URL::

   ``export DB_USER=user``
   ``export DB_PASSWORD=secret``
   ``export DB_HOST=localhost``
   ``export DB_PORT=3306``
   ``export DB_NAME=rotterdam``

Connection pooling is enabled by default and basic error handling will surface
initialisation failures early.

## Running tests

```bash
pytest
```

## Usage

Launch the command-line interface:

```bash
python main.py
```

Analysis results are written to the `output/` directory.

## API Server

A lightweight REST API can be launched to submit APKs for analysis and
retrieve risk reports.  Start the server via the CLI:

```bash
python -m cli.actions serve
```

This will start a FastAPI application on `localhost:8000` exposing endpoints:

* `POST /scans` – upload an APK and queue analysis
* `GET /scans/{id}` – check job status and view the latest risk report
* `GET /scans/{id}/report?format=json|html` – download the generated report
