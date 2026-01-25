from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from server.repositories.queries import find_paths, get_subgraph
from server.schemas.paths import PathsResponse
from server.schemas.subgraph import SubgraphResponse

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["queries"])


@router.get("/paths", response_model=PathsResponse)
async def paths_handler(
    campaign_id: str,
    from_name: str = Query(alias="from"),
    to_name: str = Query(alias="to"),
    max_hops: int = Query(default=3, ge=1, le=6),
):
    if from_name in {"", "undefined", "null"} or to_name in {"", "undefined", "null"}:
        raise HTTPException(status_code=400, detail="from/to required")
    paths = find_paths(campaign_id, from_name, to_name, max_hops)
    return {"paths": paths}


@router.get("/subgraph", response_model=SubgraphResponse)
async def subgraph_handler(
    campaign_id: str,
    entity_id: str = Query(default=None, alias="entity_id"),
    name: str = Query(default=None),
    depth: int = Query(default=2, ge=1, le=4),
    detail_level: Literal["skeleton", "summary", "full"] = Query(default="skeleton"),
):
    if entity_id in {"", "undefined", "null"}:
        entity_id = None
    if name in {"", "undefined", "null"}:
        name = None
    if not entity_id and not name:
        raise HTTPException(status_code=400, detail="entity_id or name required")
    return get_subgraph(
        campaign_id,
        entity_id=entity_id,
        name=name,
        depth=depth,
        detail_level=detail_level,
    )
