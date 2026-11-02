from fastapi import APIRouter, HTTPException, Request
import requests
import time
import uuid

from app.sharding import hash_ring
from app.memory import shard_replicas
from app.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION
)

router = APIRouter()

@router.put("/tables/{table}/records/{key}")
def create_or_update_record(table: str, key: str, body: dict, request: Request):
    endpoint = "/tables/{table}/records/{key}"
    start = time.time()
    trace_id = request.state.trace_id

    try:
        shard_id = hash_ring.get_node(key)
        if shard_id is None:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "5xx").inc()
            raise HTTPException(500, "No shards registered")

        leader = shard_replicas[shard_id]["leader"]
        if not leader:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "5xx").inc()
            raise HTTPException(500, "Leader not available")

        r = requests.put(
            f"{leader}/tables/{table}/records/{key}",
            json=body,
            headers={"X-Trace-Id": trace_id},
            timeout=3
        )

        HTTP_REQUESTS_TOTAL.labels(
            "coordinator", "PUT", endpoint, str(r.status_code)
        ).inc()

        if r.status_code >= 500:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "5xx").inc()
        elif r.status_code >= 400:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "4xx").inc()

        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)

        return r.json()

    finally:
        HTTP_REQUEST_DURATION.labels(
            "coordinator", "PUT", endpoint
        ).observe(time.time() - start)


@router.get("/tables/{table}/records/{key}")
def read_record(table: str, key: str, request: Request):
    endpoint = "/tables/{table}/records/{key}"
    start = time.time()
    trace_id = request.state.trace_id

    try:
        shard_id = hash_ring.get_node(key)
        if shard_id is None:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "5xx").inc()
            raise HTTPException(500, "No shards registered")

        replicas = []
        leader = shard_replicas[shard_id]["leader"]
        if leader:
            replicas.append(leader)
        replicas.extend(shard_replicas[shard_id]["followers"])

        responses = []

        for replica in replicas:
            try:
                r = requests.get(
                    f"{replica}/tables/{table}/records/{key}",
                    headers={"X-Trace-Id": trace_id},
                    timeout=2
                )
                if r.status_code == 200:
                    responses.append(r.json())
            except Exception:
                pass

        if not responses:
            HTTP_ERRORS_TOTAL.labels("coordinator", endpoint, "5xx").inc()
            raise HTTPException(500, "No quorum responses")

        newest = max(responses, key=lambda x: x["version"])

        HTTP_REQUESTS_TOTAL.labels(
            "coordinator", "GET", endpoint, "200"
        ).inc()

        return {
            "value": newest["value"],
            "version": newest["version"],
            "quorum_size": len(responses),
            "replicas_total": len(replicas),
        }

    finally:
        HTTP_REQUEST_DURATION.labels(
            "coordinator", "GET", endpoint
        ).observe(time.time() - start)
