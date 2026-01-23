import logging

from fastapi import APIRouter, HTTPException, Query

from server.repositories.entities import (
    create_entity,
    delete_entity,
    get_entity,
    list_entities,
    update_entity,
)
from server.repositories.sqlite_entities import get_entity_by_name as sqlite_get_entity
from server.schemas.entities import EntityCreate, EntityResponse, EntityUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns/{campaign_id}/entities", tags=["entities"])


def _enrich_entity(campaign_id: str, entity: dict) -> dict:
    """从SQLite补充属性数据"""
    sqlite_data = sqlite_get_entity(campaign_id, entity["name"])
    logger.info(f"_enrich_entity: campaign_id={campaign_id}, name={entity['name']}, sqlite_data={sqlite_data is not None}")
    if sqlite_data:
        # 过滤掉基础字段和null值
        skip_keys = {"id", "entity_id", "campaign_id", "type", "name", "created_at", "updated_at"}
        entity["properties"] = {
            k: v for k, v in sqlite_data.items()
            if k not in skip_keys and v is not None
        }
        logger.info(f"_enrich_entity: properties keys={list(entity['properties'].keys())}")
    else:
        entity["properties"] = {}
    return entity


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
    entities = list_entities(campaign_id, entity_type=type, name=name)
    result = [_enrich_entity(campaign_id, e) for e in entities]
    logger.info(f"list_entities_handler: returning {len(result)} entities")
    if result:
        logger.info(f"list_entities_handler: first entity properties={result[0].get('properties')}")
    return result


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity_handler(campaign_id: str, entity_id: str):
    entity = get_entity(campaign_id, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return _enrich_entity(campaign_id, entity)


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
