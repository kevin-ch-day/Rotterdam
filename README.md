# Rotterdam

Rotterdam is a toolkit for analyzing Android applications and devices. It provides utilities for extracting and scanning APKs, evaluating device behavior, and reporting findings.

## Development

Set up a Python environment and install the project's dependencies.

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
