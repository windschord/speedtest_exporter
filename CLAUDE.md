# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Prometheus exporter for Ookla Speedtest metrics. This is a Flask-based web service that wraps the Speedtest CLI tool and exposes network performance metrics in Prometheus format.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (requires speedtest CLI installed)
python main.py
# Server runs on http://0.0.0.0:5000
```

### Docker Development
```bash
# Build Docker image
docker build -t speedtest-exporter .

# Run container
docker run -p 5000:5000 speedtest-exporter

# The Docker image includes the Ookla speedtest CLI installation
```

### Testing the Exporter
```bash
# View available servers
curl http://localhost:5000/

# Get metrics (auto server selection)
curl http://localhost:5000/metrics

# Get metrics from specific server
curl "http://localhost:5000/metrics?server_id=48463"
```

## Architecture

### Single-File Application Structure
The entire application is contained in `main.py` with three main components:

1. **SpeedTestServer class**: Represents a speedtest server with metadata (id, name, location, country)
2. **CLI wrapper functions**:
   - `speed_test()` - Executes speedtest CLI and returns JSON results
   - `speed_test_server_list()` - Queries available speedtest servers
3. **Flask routes**:
   - `/` - Lists available servers with metric links
   - `/metrics` - Executes speedtest and returns Prometheus metrics

### Speedtest CLI Integration
- Uses Ookla's official speedtest CLI (not the Python speedtest-cli package)
- All commands include `--accept-license` flag (required for non-interactive use)
- Output format is JSON (`--format=json`)
- Server selection via `--server-id` parameter

### Prometheus Metrics Format
The `/metrics` endpoint generates Prometheus exposition format with these metric families:
- `speedtest_jitter` - Network jitter measurements
- `speedtest_latency` - Various latency metrics (ping, download, upload, with low/high/iqm variants)
- `speedtest_bandwidth` - Download/upload bandwidth in bytes per second
- `speedtest_bytes` - Total bytes transferred
- `speedtest_elapsed` - Time elapsed for operations

All metrics include common labels: `country`, `id`, `name`, `ip` (from the speedtest server)

### Prometheus Scraping Configuration
Recommended scrape configuration (from README.md):
```yaml
scrape_configs:
  - job_name: 'speedtest'
    scrape_interval: 15m  # Run speedtest every 15 minutes
    scrape_timeout: 5m    # Allow up to 5 minutes for test completion
    static_configs:
      - targets: ['<host>:5000']
```

Note: Speedtests are expensive operations - use long scrape intervals (15m+) to avoid excessive bandwidth usage.

## CI/CD

GitHub Actions workflow builds and publishes Docker images to GitHub Container Registry:
- Triggered on: pushes to main, tags starting with 'v', PRs to main, manual dispatch
- Multi-platform builds using QEMU and Docker Buildx
- Images pushed to `ghcr.io/<username>/speedtest-exporter`
- Automatic tagging based on git tags/branches

## Key Implementation Details

### Error Handling
- `SpeedTestException` raised when speedtest CLI fails (non-zero exit code)
- `/metrics` endpoint returns 500 status with error message on failures
- stderr output is logged even on successful runs (for warnings)

### Server Selection
- If no `server_id` parameter is provided, speedtest CLI auto-selects the optimal server
- The `/` route dynamically lists all available speedtest servers for manual selection

### Application Configuration
- Debug mode: disabled (`debug=False`)
- Host: `0.0.0.0` (listens on all interfaces)
- Port: 5000 (exposed in Dockerfile)
