from fastapi import APIRouter

from server.db.neo4j import ping
from server.db.schema import get_schema_status

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/schema")
async def health_schema():
    try:
        return get_schema_status()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/health/neo4j")
async def health_neo4j():
    return ping()
