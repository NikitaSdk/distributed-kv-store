from fastapi import APIRouter, HTTPException
from app.memory import shard_replicas
from app.sharding import hash_ring
from app.metrics import ACTIVE_SHARDS, REPLICAS_TOTAL

router = APIRouter()

@router.post("/shards/register")
def register_shard(body: dict):
    shard_id = body["shard_id"]
    address = body["address"]
    role = body["role"]

    if shard_id not in shard_replicas:
        shard_replicas[shard_id] = {
            "leader": None,
            "followers": []
        }
        hash_ring.add_node(shard_id)

    if role == "leader":
        shard_replicas[shard_id]["leader"] = address
    else:
        if address not in shard_replicas[shard_id]["followers"]:
            shard_replicas[shard_id]["followers"].append(address)

    # ===== METRICS UPDATE =====

    # кількість активних шард
    ACTIVE_SHARDS.set(len(shard_replicas))

    # кількість реплік у конкретному шарді
    replicas_count = 0
    if shard_replicas[shard_id]["leader"]:
        replicas_count += 1
    replicas_count += len(shard_replicas[shard_id]["followers"])

    REPLICAS_TOTAL.labels(shard_id).set(replicas_count)

    return {
        "status": "registered",
        "shard_id": shard_id,
        "replicas": shard_replicas[shard_id]
    }


@router.get("/shards/{shard_id}/followers")
def get_followers(shard_id: str):
    if shard_id not in shard_replicas:
        raise HTTPException(404, "Shard not found")

    return {
        "followers": shard_replicas[shard_id]["followers"]
    }
