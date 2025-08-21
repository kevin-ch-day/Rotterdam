# Rotterdam Architecture

Rotterdam is composed of modular layers that cooperate to analyze Android applications and devices.

## Command Line Interface

The interactive CLI in `cli/` provides menus for interacting with connected devices, running static or dynamic analysis, and starting the API server. Actions under `cli/actions/` wrap the analysis pipelines and persist results in the repository.

## Static Analysis Pipeline

The static pipeline under `platform/android/analysis/static/` decompiles APKs, extracts manifest data, searches for secrets, optionally applies YARA rules, and feeds metrics to the risk‑scoring model. The pipeline's output is a report written to `output/<timestamp>/`.

## Dynamic Sandbox

**Note:** The dynamic sandbox is parked for the MVP. See [sandbox/PARKED.md](../sandbox/PARKED.md). Avoid modifying or relying on this component until work resumes.

Dynamic analysis lives in `platform/android/analysis/dynamic/`. The `runner.py` module simulates execution of an APK with Frida instrumentation hooks defined in `frida/`. Observed runtime events are converted into metrics that complement static findings.

## Risk Scoring

The scoring model in `platform/android/analysis/static/scoring/risk_score.py` combines weighted static and dynamic metrics into a normalized 0‑100 score with a human‑readable rationale.

## API Server

A FastAPI application under `server/` exposes REST endpoints for submitting jobs, retrieving reports, querying analytics, and system status. Middleware adds request IDs and basic authentication/rate limiting. Static files for the web UI must reside under the repository's `ui/` directory so they can be mounted at `/ui` and `/static`.

## Data Flow

1. A user launches the CLI and selects an action.
2. The CLI invokes static or dynamic analysis modules.
3. Analysis modules generate metrics and artifacts in `output/` and call the risk scorer.
4. Results are persisted via the `storage` repository and can be served through the API server.

