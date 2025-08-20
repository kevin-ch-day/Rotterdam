# Rotterdam

Rotterdam is a toolkit for analyzing Android applications and devices. It provides utilities for extracting and scanning APKs, evaluating device behavior, and reporting findings.

## Quick start

On Fedora systems the helper scripts make it easy to set up and launch the CLI:

```bash
./setup.sh              # install dependencies and create virtual environment
./run.sh                # start the interactive CLI

# optional helpers
./setup.sh --force-venv   # recreate the virtual environment
./setup.sh --skip-system  # skip dnf package installation
./run.sh --setup          # run setup before launching
```

## Setup

The helper script targets Fedora but the same dependencies are available on
other platforms.

### Fedora

Installed automatically by `setup.sh`:

```
python3 python3-virtualenv adb aapt2 apktool java-11-openjdk yara
```

### Debian/Ubuntu

```
sudo apt-get install python3 python3-venv adb aapt apktool openjdk-11-jdk libyara-dev
```

### macOS (Homebrew)

```
brew install python3 adb aapt apktool openjdk@11 yara
```

Optional tools such as Frida or MySQL can be installed separately if needed.

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

### CLI Examples

#### Static APK analysis

```
python main.py
# Analysis → Analyze APK → select /path/to/app.apk
# Report written to output/<timestamp>/report.json
```

#### Device scan

```
python -m cli.actions list-packages <device-serial>
# Outputs list of installed packages and can export to CSV/JSON
```

#### Sandbox analysis

```
python main.py
# Analysis → Sandbox APK → select /path/to/app.apk
# See docs/dynamic-analysis.md for hook details
```

### Database status

The interactive menu provides a **Database** option that performs a
connectivity check, reports table counts and lists the most recent analyses.
This helps surface misconfiguration or missing tables early during
development.

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

Example requests:

```
# submit an APK for analysis
curl -F "file=@app.apk" http://localhost:8000/scans
# => {"id":1,"status":"queued"}

# poll job status
curl http://localhost:8000/scans/1
# => {"id":1,"status":"complete"}

# download the JSON report
curl http://localhost:8000/scans/1/report?format=json
```

Endpoints apply simple request‑ID, authentication, and rate‑limiting middleware.

## Architecture

High-level module interactions are documented in
[docs/architecture.md](docs/architecture.md).

Additional reference material:

- [Dynamic analysis](docs/dynamic-analysis.md)
- [Risk scoring](docs/risk-scoring.md)
