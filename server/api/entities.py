from fastapi import APIRouter, HTTPException, Query

from server.repositories.entities import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_entity,
)
from server.schemas.entities import EntityCreate, EntityResponse, EntityUpdate

router = APIRouter(prefix="/api/campaigns/{campaign_id}/entities", tags=["entities"])


@router.post("", response_model=EntityResponse)
async def create_entity_handler(campaign_id: str, payload: EntityCreate):
    entity = create_entity(
        campaign_id,
        payload.type,
        payload.name,
        payload.properties,
        payload.metadata,
    )
    return entity


@router.get("", response_model=list[EntityResponse])
async def list_entities_handler(
    campaign_id: str,
    type: str | None = Query(default=None),
    name: str | None = Query(default=None),
):
    return list_entities(campaign_id, entity_type=type, name=name)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity_handler(campaign_id: str, entity_id: str):
    entity = get_entity(campaign_id, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity_handler(
    campaign_id: str,
    entity_id: str,
    payload: EntityUpdate,
):
    updates = payload.model_dump(exclude_unset=True)
    entity = update_entity(campaign_id, entity_id, updates)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/{entity_id}")
async def delete_entity_handler(campaign_id: str, entity_id: str):
    deleted = delete_entity(campaign_id, entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "deleted"}
