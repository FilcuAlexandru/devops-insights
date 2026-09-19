# Monitoring

The configuration that Docker Compose mounts into Prometheus and Grafana. Nothing here needs to be
set up by hand: start the stack and the datasource and the dashboard are already there.

```
monitoring/
├── prometheus/
│   ├── prometheus.yml   what to scrape: the backend, the collector and Prometheus itself
│   └── web.yml          the login for Prometheus (admin / admin, stored as a bcrypt hash)
└── grafana/
    ├── provisioning/
    │   ├── datasources/prometheus.yml   the Prometheus datasource, with its login already filled in
    │   └── dashboards/dashboards.yml    tells Grafana where to find the dashboards
    └── dashboards/devops-insights.json  the dashboard itself
```

## Good to know

- **Prometheus is password protected**, so Grafana's datasource carries the same credentials, and
  even Prometheus scraping itself needs them. It is a small thing, but it means every component
  with a login really uses `admin / admin`.
- **The dashboard exists twice.** The Helm chart can only read files inside its own folder, so a
  copy lives in `deploy/helm/devops-insights/files/`. After editing the dashboard run
  `make sync-monitoring`. CI fails when the two copies differ, so you can't forget.
- **Every panel query was checked** against a running Prometheus with real data.

What the metrics mean, and how to change the password, is in
[docs/observability.md](../docs/observability.md).
