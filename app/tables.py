from fastapi import APIRouter, HTTPException
from app.memory import tables, compound_tables

router = APIRouter()

@router.post("/tables")
def create_table(body: dict):
    name = body["table_name"]

    if name in tables:
        raise HTTPException(400, "Table already exists")

    tables[name] = {}
    compound_tables[name] = {}

    return {"status": "table_created", "table": name}
