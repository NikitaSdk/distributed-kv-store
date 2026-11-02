from prometheus_client import Counter, Histogram, Gauge


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"]
)

HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["service", "endpoint", "status_class"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "method", "endpoint"],
    buckets=(
        0.05, 0.1, 0.25, 0.5,
        0.75, 1, 2.5, 5, 10
    )
)



ACTIVE_SHARDS = Gauge(
    "active_shards",
    "Number of active shards"
)

REPLICAS_TOTAL = Gauge(
    "replicas_total",
    "Total replicas per shard",
    ["shard_id"]
)

REPLICA_LAG = Gauge(
    "replica_lag_versions",
    "Replication lag in versions",
    ["shard_id", "replica"]
)
