# speedtest_exporter

[![Docker Image CI](https://github.com/windschord/speedtest_exporter/actions/workflows/docker-image.yml/badge.svg)](https://github.com/windschord/speedtest_exporter/actions/workflows/docker-image.yml)

# prometheus.yml

```yaml
global:
  scrape_interval: 10s

scrape_configs:
  - job_name: 'speedtest'
    scrape_interval: 15m
    scrape_timeout: 5m
    # params:
    #   server_id: ['48463']
    static_configs:
      - targets: ['192.168.11.54:5000']
```