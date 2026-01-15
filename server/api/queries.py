from fastapi import APIRouter, Query

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
    paths = find_paths(campaign_id, from_name, to_name, max_hops)
    return {"paths": paths}


@router.get("/subgraph", response_model=SubgraphResponse)
async def subgraph_handler(
    campaign_id: str,
    entity_id: str = Query(alias="entity_id"),
    depth: int = Query(default=2, ge=1, le=4),
):
    return get_subgraph(campaign_id, entity_id, depth)
