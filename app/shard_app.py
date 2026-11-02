import os
import time
import requests
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION,
    REPLICA_LAG,
)

app = FastAPI(title="Shard Node")


storage = {}
event_log = []           # leader only (для resync)

OFFSET_FILE = "/data/offset.txt"
last_applied_version = 0.0

COORDINATOR_URL = os.getenv("COORDINATOR_URL")
SHARD_ADDRESS = os.getenv("SHARD_ADDRESS")
SHARD_ID = os.getenv("SHARD_ID")
ROLE = os.getenv("ROLE")
LEADER_ADDRESS = os.getenv("LEADER_ADDRESS")



def load_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            return float(f.read())
    except Exception:
        return 0.0


def save_offset(offset: float):
    os.makedirs(os.path.dirname(OFFSET_FILE), exist_ok=True)
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))



@app.on_event("startup")
def startup():
    global last_applied_version
    last_applied_version = load_offset()

    payload = {
        "shard_id": SHARD_ID,
        "address": SHARD_ADDRESS,
        "role": ROLE,
    }

    for _ in range(20):
        try:
            requests.post(
                f"{COORDINATOR_URL}/shards/register",
                json=payload,
                timeout=3
            )
            break
        except Exception:
            time.sleep(2)

    if ROLE == "follower":
        resync_from_leader()



@app.put("/tables/{table}/records/{key}")
async def put_record(table: str, key: str, request: Request):
    endpoint = "/tables/{table}/records/{key}"
    start = time.time()

    try:
        if ROLE != "leader":
            raise HTTPException(403, "Writes allowed only on leader")

        body = await request.json()
        value = body.get("value")

        version = time.time()  # ✅ TIMESTAMP

        record = {
            "value": value,
            "version": version
        }

        storage.setdefault(table, {})[key] = record

        event = {
            "table": table,
            "key": key,
            "record": record
        }

        event_log.append(event)
        replicate_to_followers(event)

        return {"stored": True, "version": version}

    finally:
        HTTP_REQUEST_DURATION.labels(
            "shard", "PUT", endpoint
        ).observe(time.time() - start)



def replicate_to_followers(event: dict):
    try:
        r = requests.get(
            f"{COORDINATOR_URL}/shards/{SHARD_ID}/followers",
            timeout=3
        )
        followers = r.json().get("followers", [])
    except Exception:
        return

    for follower in followers:
        try:
            requests.post(
                f"{follower}/internal/replicate",
                json=event,
                timeout=2
            )
        except Exception:
            pass



@app.post("/internal/replicate")
def replicate(event: dict):
    global last_applied_version

    table = event["table"]
    key = event["key"]
    incoming = event["record"]

    local = storage.get(table, {}).get(key)

    # ===== LAST-WRITE-WINS =====
    if local is None or incoming["version"] > local["version"]:
        storage.setdefault(table, {})[key] = incoming

        last_applied_version = incoming["version"]
        save_offset(last_applied_version)

        REPLICA_LAG.labels(
            shard_id=SHARD_ID,
            replica=SHARD_ADDRESS
        ).set(0)

        return {
            "status": "applied",
            "version": incoming["version"]
        }

    return {
        "status": "ignored",
        "version": local["version"]
    }



@app.get("/tables/{table}/records/{key}")
def get_record(table: str, key: str):
    endpoint = "/tables/{table}/records/{key}"
    start = time.time()

    try:
        if table not in storage or key not in storage[table]:
            raise HTTPException(404, "Not found")

        record = storage[table][key]

        return {
            "value": record["value"],
            "version": record["version"],
            "role": ROLE,
        }

    finally:
        HTTP_REQUEST_DURATION.labels(
            "shard", "GET", endpoint
        ).observe(time.time() - start)



@app.get("/internal/log")
def get_log(from_version: float = 0.0):
    if ROLE != "leader":
        raise HTTPException(403, "Only leader has log")

    return [
        e for e in event_log
        if e["record"]["version"] > from_version
    ]



@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )



def resync_from_leader():
    global last_applied_version

    if not LEADER_ADDRESS:
        return

    try:
        r = requests.get(
            f"{LEADER_ADDRESS}/internal/log",
            params={"from_version": last_applied_version},
            timeout=5
        )
        events = r.json()
    except Exception:
        return

    for event in events:
        record = event["record"]
        storage.setdefault(event["table"], {})[event["key"]] = record
        last_applied_version = record["version"]
        save_offset(last_applied_version)




