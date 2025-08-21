# Bring-up Checklist

Use this checklist when preparing a fresh environment or verifying a clean setup.

## Setup
1. Install dependencies and create the virtual environment:
   ```bash
   ./setup.sh
   ```
2. Re-run with `--force-venv` if the environment needs to be rebuilt.

## Run the CLI
1. Launch the interactive interface:
   ```bash
   ./run.sh
   ```
2. From the menu, select **Database** to confirm connectivity and table counts.

## Run the API Server
1. Start the server via the CLI action:
   ```bash
   python -m cli.actions serve
   ```
2. Verify the server is healthy:
   ```bash
   curl http://localhost:8765/_healthz
   ```

## Static Analysis Dry Run
1. Execute a sample static analysis to ensure tools are wired correctly:
   ```bash
   python -m cli.actions analyze path/to/app.apk
   ```
2. Confirm a report appears under `output/<timestamp>/`.
