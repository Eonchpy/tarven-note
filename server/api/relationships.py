from fastapi import APIRouter, HTTPException, Query

from server.repositories.relationships import (
    create_relationship,
    delete_relationship,
    list_relationships,
)
from server.schemas.relationships import RelationshipCreate, RelationshipResponse

router = APIRouter(prefix="/api/campaigns/{campaign_id}/relationships", tags=["relationships"])


@router.post("", response_model=RelationshipResponse)
async def create_relationship_handler(campaign_id: str, payload: RelationshipCreate):
    relationship = create_relationship(
        campaign_id,
        payload.from_entity_id,
        payload.to_entity_id,
        payload.type,
        payload.properties,
    )
    if not relationship:
        raise HTTPException(status_code=404, detail="Entity not found")
    return relationship


@router.get("", response_model=list[RelationshipResponse])
async def list_relationships_handler(
    campaign_id: str,
    from_entity_id: str | None = Query(default=None),
    to_entity_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
):
    return list_relationships(
        campaign_id,
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        relationship_type=type,
    )


@router.delete("/{relationship_id}")
async def delete_relationship_handler(campaign_id: str, relationship_id: str):
    deleted = delete_relationship(campaign_id, relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"status": "deleted"}
