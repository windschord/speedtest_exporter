# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

speedtest_exporter is a Prometheus exporter for Ookla Speedtest CLI. It's a Flask application that wraps the `speedtest` command-line tool and exposes network speed test results as Prometheus metrics.

## Development Commands

### Running the Application

**Local development:**
```bash
python main.py
```
The server runs on port 5000 by default.

**Docker build and run:**
```bash
docker build -t speedtest-exporter .
docker run -p 5000:5000 speedtest-exporter
```

**Testing the application:**
```bash
# View available servers
curl http://localhost:5000/

# Run speed test with auto-selected server
curl http://localhost:5000/metrics

# Run speed test with specific server
curl http://localhost:5000/metrics?server_id=48463
```

### Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

The Ookla speedtest CLI must be installed (handled automatically in Docker, but needs manual installation for local development).

## Architecture

### Single-File Application

The entire application is in `main.py` (~110 lines). Key components:

1. **SpeedTestServer class**: Represents a speedtest server with metadata (id, name, location, country)
2. **speed_test() function**: Executes speedtest CLI via subprocess with `--accept-license --format=json`
3. **speed_test_server_list() function**: Retrieves available servers from speedtest CLI
4. **Flask routes**:
   - `/` - Index page showing links to all available speedtest servers
   - `/metrics` - Prometheus metrics endpoint (accepts optional `server_id` query param)

### Metrics Structure

The exporter exposes these Prometheus metric families:

- `speedtest_jitter` - Ping jitter
- `speedtest_latency` - Various latency measurements (ping, download, upload with low/high/iqm)
- `speedtest_bandwidth` - Download/upload bandwidth
- `speedtest_bytes` - Download/upload bytes transferred
- `speedtest_elapsed` - Download/upload elapsed time

All metrics include labels: `country`, `id` (server), `name` (server), `ip` (server), and `type` (measurement type).

### CLI Dependency

The application depends on Ookla's speedtest CLI tool, which must:
- Accept the license agreement (via `--accept-license` flag)
- Support JSON output format (`--format=json`)
- Support server selection (`--server-id={id}`)

### Error Handling

- SpeedTestException is raised for speedtest CLI failures
- The /metrics endpoint returns 500 status with error message on exceptions
- stderr from speedtest is printed but doesn't fail the request

## Deployment

### Docker

The Dockerfile:
- Uses python:3.11-slim base image
- Installs Ookla speedtest CLI from their official repository
- Exposes port 5000
- Single-stage build for simplicity

### CI/CD

GitHub Actions workflow (`.github/workflows/docker-image.yml`):
- Triggers on push to main, tag push (v*), PRs, and manual dispatch
- Builds multi-platform Docker images using buildx
- Publishes to GitHub Container Registry (ghcr.io)
- Uses GitHub Actions cache for layer caching

## Prometheus Integration

Expected scrape configuration:
```yaml
scrape_configs:
  - job_name: 'speedtest'
    scrape_interval: 15m  # Speed tests are slow
    scrape_timeout: 5m    # Allow time for test completion
    static_configs:
      - targets: ['<host>:5000']
```

The scrape interval should be long (15m+) since speed tests take time and frequent testing can impact network usage.
