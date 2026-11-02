from fastapi import FastAPI, Response, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import uuid

from app.tables import router as tables_router
from app.records import router as records_router
from app.records_compound import router as compound_router
from app.shards import router as shards_router

app = FastAPI(
    title="Coordinator (Sharded Mode)",
    version="2.0"
)

# ---------- TRACE ID MIDDLEWARE ----------
@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response

# ---------- ROUTERS ----------
app.include_router(shards_router)
app.include_router(tables_router)
app.include_router(records_router)
app.include_router(compound_router)

# ---------- METRICS ----------
@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
