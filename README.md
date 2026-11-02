# Distributed Key-Value Store

**A sharded, replicated key-value database** (university course, KPI, 2025). A coordinator routes requests by consistent hashing to shards; each shard has a leader and two followers that receive replicated writes.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)

## Architecture

```
client ──► coordinator (consistent hashing)
              ├─► shard 1: leader ──► follower 1, follower 2
              └─► shard 2: leader ──► follower 1, follower 2
Prometheus ◄── /metrics      Grafana dashboards
```

## Features

- **Tables and records:** simple keys and compound keys (partition + sort key), full CRUD.
- **Sharding** with a consistent-hash ring; shards register themselves with the coordinator.
- **Leader → follower replication** with a replication log; quorum reads return the newest version.
- **Trace ID** on every request, Prometheus metrics, Grafana dashboards.
- **Load benchmark** (`benchmark.py`) with concurrent reads and writes.

## Run

```bash
docker compose up --build
docker compose -f docker-compose.monitoring.yml up   # Prometheus + Grafana
python benchmark.py
```

## Lab reports

Built across three labs of the Cloud Technologies course. Reports (PDF, Ukrainian) are in [`docs/`](docs): API and sharding · replication · monitoring.
