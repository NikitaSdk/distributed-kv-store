from fastapi import APIRouter, HTTPException
from app.memory import compound_tables

router = APIRouter()

@router.put("/tables/{table}/records/{partition}/{sort}")
def put_compound(table, partition, sort, body):
    if table not in compound_tables:
        raise HTTPException(404, "Table not found")

    compound_tables[table].setdefault(partition, {})
    compound_tables[table][partition][sort] = body["value"]
    return {"status": "ok"}

@router.get("/tables/{table}/records/{partition}/{sort}")
def get_compound(table, partition, sort):
    if (
        table not in compound_tables
        or partition not in compound_tables[table]
        or sort not in compound_tables[table][partition]
    ):
        raise HTTPException(404, "Record not found")

    return {
        "partition_key": partition,
        "sort_key": sort,
        "value": compound_tables[table][partition][sort]
    }

@router.delete("/tables/{table}/records/{partition}/{sort}")
def delete_compound(table, partition, sort):
    if (
        table not in compound_tables
        or partition not in compound_tables[table]
        or sort not in compound_tables[table][partition]
    ):
        raise HTTPException(404, "Record not found")
    del compound_tables[table][partition][sort]
    return {"status": "deleted"}
