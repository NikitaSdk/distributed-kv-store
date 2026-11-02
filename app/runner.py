import os
import uvicorn

mode = os.getenv("MODE", "coordinator")

if mode == "coordinator":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
else:
    uvicorn.run("app.shard_app:app", host="0.0.0.0", port=8000)
